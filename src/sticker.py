from PIL import Image
import pytesseract
from pathlib import Path
from rapidfuzz import process, fuzz
import spacy, re


class Sticker:

    __recipient_name = ""

    # Lista de moradores para teste (apenas para fuzzy matching)
    TEST_MORADORES = [
        "Maurício de Souza",
        "João Dias",
        "Maria Oliveira",
        "Ruan Rodrigues Da Silva",
        "Ana dos Anjos",
        "Ana Aguiar Moraes"
    ]

    # Stop words irrelevantes
    STOP_WORDS = [
        "Shopee", "XPRESS", "LEVAR", "Agência", "Soc", "Separação",
        "Correios", "Pedido", "NF", "Nome Legível",
        "Documento", "DANFE", "Volume", "Envio",
        "Recebimento", "Confirmação", "Expressa", "Finalizado",
        "Rastreio", "Entrega", "Etiqueta", "Pacote",
        "Simplificado", "Saída", "Peso", "Pedido", "Volume",
        "AMAZON", "Loggi", "SEDEX", "Shein", "Objeto"
    ]

    STOP_NAME_TOKENS = {"casa", "cep", "endereco", "entrega", "pedido", "ltda", "apartamento", "bloco"}

    @staticmethod
    def sanitize(text: str, stop_words=STOP_WORDS, min_words=2, for_ner=True) -> str:
        """
        Limpa o texto do OCR para NER ou exibição:
        
        - Remove caracteres irrelevantes (mantendo letras, números)
        - Normaliza múltiplos espaços
        - Remove stop words irrelevantes
        - Remove números irrelevantes:
            * longos (>5 dígitos)
            * números com letras (ex: 230811BNH7M33K)
        - Retorna vazio se a linha tiver menos que `min_words` palavras
        
        Parâmetro `for_ner`:
            - True: substitui vírgulas e pontos por espaço para facilitar tokenização do NER
            - False: mantém pontuação original
        """
        
        # Detectar CEPs e juntar dígitos
        def normalize_ceps(text: str) -> str:
            # Regex: 5 dígitos + opcional hífen/espaço + 3 dígitos
            def cep_replacer(match):
                digits = re.sub(r'\D', '', match.group())  # remove tudo que não é número
                if len(digits) == 8:
                    return digits
                return match.group()  # se não for 8 dígitos, mantém como está

            return re.sub(r'\b\d{5}[-\s]?\d{3}\b', cep_replacer, text)
        
         # --- Normalizar "s/n" para "semnumero" ---
        def normalize_sem_numero(text: str) -> str:
            # cobre variações: s/n, S/N, s-n, s n, sem numero, sem número
            return re.sub(
                r"\b(s[\s\-\/]?n|sem\s+n[úu]mero)\b",
                "semnumero",
                text,
                flags=re.IGNORECASE
            )

        
        if stop_words is None:
            stop_words = []
            
        # Normalizar "sem número" primeiro
        text = normalize_sem_numero(text)

        # Remover stop words
        for sw in stop_words:
            pattern = re.compile(rf"{re.escape(sw)}\b", re.IGNORECASE)
            text = pattern.sub("", text)

        # Remover caracteres não alfanuméricos, mantendo vírgulas e pontos
        text = re.sub(r"[^a-zA-Z0-9á-úÁ-ÚçÇ.,\s]", " ", text)

        # Substituir vírgulas/pontos por espaço apenas se for para NER
        if for_ner:
            text = re.sub(r"[.,]", " ", text)

        # Normalizar múltiplos espaços
        text = re.sub(r"\s+", " ", text).strip()

        # Remover números com letras (códigos, rastreio)
        text = re.sub(r'\b\w*\d+\w*\b', lambda m: '' if re.search(r'\D', m.group()) else m.group(), text)

        # Remover números puros longos (>5 dígitos)
        text = re.sub(r'\b\d{6,}\b', '', text)

        # Remover palavras de 2 caracteres
        text = " ".join([w for w in text.split() if len(w) > 2])

        # Remover links
        text = re.sub(r'\b\w+\.\w+(\.\w+)?\b', '', text)

        # Normalizar múltiplos espaços novamente
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Dentro do sanitize
        text = normalize_ceps(text)

        # Descartar linhas muito curtas
        if len(text.split()) < min_words:
            return ""

        return text


    def __init__(self, image: str):
        base_dir = Path(__file__).parent
        image_path = base_dir.parent / "assets" / image

        img = Image.open(str(image_path))
        self.__text: str = str(pytesseract.image_to_string(img, lang="por"))

        # carregar modelo treinado de nomes
        model_path = base_dir.parent / "models" / "name_ner"
        self.nlp = spacy.load(model_path)

    @property
    def text(self):
        return self.__text

    @property
    def recipient_name(self):
        return self.__recipient_name

    def extract_recipient_name(self):
        """
        Extrai o nome do destinatário usando:
        1. NER para detectar candidatos
        2. Fuzzy matching para mapear candidatos aos nomes reais
        """
        # Quebrar em linhas e limpar
        lines = [Sticker.sanitize(l, stop_words=Sticker.STOP_WORDS) for l in self.__text.splitlines()]
        useful_lines = [l for l in lines if l]

        # Combinar linhas curtas (pode formar fragmentos de nomes)
        combined_lines = []
        buffer = ""
        for line in useful_lines:
            if buffer:
                buffer += " " + line
            else:
                buffer = line
            if len(buffer.split()) >= 3:
                combined_lines.append(buffer)
                buffer = ""
        if buffer:
            combined_lines.append(buffer)

        # Rodar NER
        candidates = []
        doc_full = self.nlp("\n".join(combined_lines))
        for ent in doc_full.ents:
            if ent.label_ == "PERSON":
                candidates.append(ent.text)

        for line in combined_lines:
            doc = self.nlp(line)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    candidates.append(ent.text)

        candidates = list(set(candidates))

        print("\n[DEBUG] Candidatos detectados pelo NER:")
        for c in candidates:
            print("   🧍", c)

        # Pré-filtrar candidatos sem excluir completamente
        cleaned_candidates = []
        for c in candidates:
            tokens = [t for t in c.split() if t.lower() not in self.STOP_NAME_TOKENS]
            cleaned = " ".join(tokens)
            if len(cleaned.split()) > 1 and not any(ch.isdigit() for ch in cleaned):
                cleaned_candidates.append(cleaned)


        # Fuzzy matching para todos os candidatos
        best_candidate, best_match, best_score = None, None, 0
        for cand in candidates:
            match = process.extractOne(
                cand,
                self.TEST_MORADORES,
                scorer=fuzz.token_set_ratio
            )
            # Debug detalhado para todos os candidatos
            if match:
                print(f"[DEBUG] 🔎 Candidato: '{cand}' → Melhor match: '{match[0]}' (score {match[1]})")

            if match and match[1] > best_score:
                best_candidate = cand
                best_match = match
                best_score = match[1]

        # Definir o nome final
        if best_match and best_score > 70:
            # Sempre usar o nome real da lista de moradores
            self.__recipient_name = best_match[0]
            print(f"[INFO] Nome final detectado pelo Fuzzy: {self.__recipient_name}")
        else:
            # Fallback: pegar o candidato do NER (ou vazio se não houver)
            self.__recipient_name = best_candidate if best_candidate else ""
            print(f"[INFO] Fallback nome detectado: {self.__recipient_name}")

    def __str__(self):
        return self.text
