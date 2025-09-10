from PIL import Image
import pytesseract
from pathlib import Path
from rapidfuzz import process
import spacy, re


class Sticker:

    __recipient_name = ""

    # Lista de moradores para teste (apenas para fuzzy matching)
    TEST_MORADORES = [
        "Maurício de Souza",
        "João Dias",
        "Maria Oliveira",
        "Ruan Rodrigues Da Silva",
        "Ana dos Anjos"
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

    @staticmethod
    def sanitize(text: str, stop_words=None, min_words=2) -> str:
        """
        Limpa o texto de forma abrangente:
        - Remove caracteres estranhos (mantendo letras, números, vírgulas e pontos)
        - Normaliza múltiplos espaços
        - Remove stop words irrelevantes
        - Remove palavras de 2 caracteres
        - Remove números irrelevantes:
            * números longos (>5 dígitos)
            * números com letras (ex: 230811BNH7M33K)
        - Retorna vazio se a linha tiver menos que `min_words` palavras
        """
        if stop_words is None:
            stop_words = []
            
        # Remover stop words
        for sw in stop_words:
            pattern = re.compile(rf"{re.escape(sw)}\b", re.IGNORECASE)
            text = pattern.sub("", text)


        # Remover caracteres não alfanuméricos, exceto espaços, vírgulas e pontos
        text = re.sub(r"[^a-zA-Z0-9á-úÁ-ÚçÇ.,\s]", " ", text)

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

    def extract_recipient(self):
        """
        Extrai o nome do destinatário usando:
        1. Sanitização linha a linha
        2. NER treinado
        3. Fallback com fuzzy matching nas linhas úteis
        """
        # Quebrar em linhas e limpar
        lines = [Sticker.sanitize(l, stop_words=Sticker.STOP_WORDS) for l in self.__text.splitlines()]
        useful_lines = [l for l in lines if l]  # mantém só linhas não vazias


        # Combinar linhas curtas próximas (possível fragmento de nome)
        combined_lines = []
        buffer = ""
        for line in useful_lines:
            if buffer:
                buffer += " " + line
            else:
                buffer = line
            # se a linha combinada tiver mais de 2 palavras, considerar
            if len(buffer.split()) >= 3:
                combined_lines.append(buffer)
                buffer = ""
        if buffer:
            combined_lines.append(buffer)

        # Rodar NER no texto completo e nas linhas combinadas
        candidates = []

        # 1. NER no texto completo
        doc_full = self.nlp("\n".join(combined_lines))
        for ent in doc_full.ents:
            if ent.label_ == "PERSON":
                candidates.append(ent.text)

        # 2. NER linha a linha (fallback adicional)
        for line in combined_lines:
            doc = self.nlp(line)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    candidates.append(ent.text)

        # Filtrar candidatos válidos (descarta números e fragmentos curtos)
        candidates = [c for c in candidates if len(c.split()) > 1 and not any(ch.isdigit() for ch in c)]

        print("\n[DEBUG] Candidatos detectados pelo NER:")
        for c in candidates:
            print("   🧍", c)

        # Se houver candidatos, escolher o melhor via fuzzy
        if candidates:
            
            best_line = max(
                candidates,
                key=lambda l: process.extractOne(l, self.TEST_MORADORES)[1],
                default=""
            )
        else:
            # fallback absoluto: pegar linha útil mais longa
            best_line = max(useful_lines, key=lambda l: len(l.split()), default="")

        if best_line:
            best_match = process.extractOne(best_line, self.TEST_MORADORES)
            if best_match and best_match[1] > 85:
                self.__recipient_name = best_match[0]
            else:
                self.__recipient_name = best_line
        else:
            self.__recipient_name = ""

    def __str__(self):
        return self.text
