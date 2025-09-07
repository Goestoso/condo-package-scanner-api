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
        "LM Hub", "Correios", "Pedido:", "NF:", "BR", "O)", "Nome Legível",
        "Documento", "DANFE SIMPLIFICADO"
    ]

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Remove caracteres estranhos, múltiplos espaços e símbolos desnecessários.
        Mantém letras, números e pontuação básica.
        """
        # remover caracteres não alfanuméricos, exceto espaços, vírgulas e pontos
        text = re.sub(r"[^a-zA-Z0-9á-úÁ-ÚçÇ.,\s]", " ", text)
        # substituir múltiplos espaços por um único
        text = re.sub(r"\s+", " ", text)
        return text.strip()

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
        lines = [self.sanitize(l.strip()) for l in self.__text.splitlines() if l.strip()]
        useful_lines = []
        for line in lines:
            if any(sw.lower() in line.lower() for sw in self.STOP_WORDS):
                continue
            if len(line.split()) < 2:  # descartar linhas muito curtas
                continue
            useful_lines.append(line)

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
