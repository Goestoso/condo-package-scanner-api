from PIL import Image
import pytesseract
from pathlib import Path
from rapidfuzz import process
import re

class Sticker:

    __recipient_name = ""
    __recipient_residence = ""
    
    # Lista de moradores para teste (substituir pelo banco depois)
    TEST_MORADORES = [
        "Maurício de Souza",
        "João Dias",
        "Maria Oliveira",
        "Ruan Rodrigues da Silva"
    ]

    @property
    def text(self): 
        return self.__text

    @property
    def recipient_name(self):
        return self.__recipient_name

    @property
    def recipient_residence(self):
        return self.__recipient_residence

    def __init__(self, image:str):
        base_dir = Path(__file__).parent
        image_path = base_dir.parent / "assets" / image

        # --- Abrir imagem ---
        img = Image.open(str(image_path))    

        # --- Extrair texto em português ---
        self.__text: str = str(pytesseract.image_to_string(img, lang="por"))

    def extract_recipient(self):
        """
        Extrai nome e endereço do destinatário de forma layout-agnostic,
        usando CEP como âncora e fuzzy matching para o nome.
        """
        # filtrar linhas vazias
        lines = [l.strip() for l in self.__text.splitlines() if l.strip()]

        # criar bloco de texto útil, ignorando stop words de transportadora
        stop_words = ["Shopee", "XPRESS", "LEVAR", "Agência", "Soc", "Separação", "LM Hub", "Correios"]
        useful_lines = [l for l in lines if not any(sw.lower() in l.lower() for sw in stop_words)]

        block_text = " ".join(useful_lines)

        # --- Extrair CEP como âncora do endereço ---
        cep_match = re.search(r"\d{5}-\d{3}", block_text)
        if cep_match:
            cep_index = cep_match.start()
            # pegar algumas palavras antes e depois do CEP como endereço
            words = block_text.split()
            # encontrar índice da palavra que contém o CEP
            cep_word_index = next(i for i, w in enumerate(words) if cep_match.group() in w)
            # endereço: 8 palavras antes do CEP até 5 palavras depois (ajustável)
            start_index = max(0, cep_word_index - 8)
            end_index = min(len(words), cep_word_index + 5)
            address_words = words[start_index:end_index]
            self.__recipient_residence = " ".join(address_words)
        else:
            self.__recipient_residence = ""

        # --- Extrair nome via fuzzy matching ---
        best_match = process.extractOne(block_text, self.TEST_MORADORES)
        if best_match and best_match[1] > 70:
            self.__recipient_name = best_match[0]
        else:
            self.__recipient_name = ""

    
    def __str__(self):
        return self.text
