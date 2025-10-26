from src.condo_package_label import CondoPackageLabel
from src.utils.logger import get_logger
from src.utils.normalize import normalize_full
from src.utils.sanitize import sanitize_full, sanitize_edges
from pathlib import Path
import spacy, re

class Extractor(CondoPackageLabel):

    __MODEL_NAME_PATH = Path(__file__).parent.parent / "models" / "name_ner" / "model-last"
    __MODEL_ADDRESS_PATH = Path(__file__).parent.parent / "models" / "address_ner" / "model-last"

    @property
    def candidates_name(self):
        # retorna lista ordenada sem duplicatas
        return sorted(self.__candidates_name)
    
    @property
    def candidates_address(self):
        return {k: sorted(v) for k, v in self.__candidates_address.items()}

    def __init__(self, img: str):
        super().__init__(img)
        self.logger = get_logger(self.__class__.__name__)
        
        self.__candidates_name = set()
        self.__candidates_address = {"STREET": set(), "NUMBER": set(), "COMPLEMENT": set(), "CITY": set(), "STATE": set()}

        self.logger.info("Carregando modelos NER...")
        self.nlp_name = spacy.load(self.__MODEL_NAME_PATH)
        self.nlp_address = spacy.load(self.__MODEL_ADDRESS_PATH)
        self.logger.info("Modelos carregados com sucesso.")

    def extract_recipient_name(self):
        """Extrai candidatos a nomes usando NER. Não valida ou faz fuzzy matching."""
        text_clean = normalize_full(self.text, for_address=False)
        self.logger.debug(f"extract_recpient_name() -> Pipeline de sanitização concluído: {text_clean}")
        text_clean = sanitize_full(text_clean, remove_acc=False)
        self.logger.debug(f"extract_recpient_name() -> Pipeline de normalização concluído: {text_clean}")

        doc = self.nlp_name(text_clean)
        self.__candidates_name = {ent.text for ent in doc.ents if ent.label_ == "PERSON"}

        self.logger.info(f"Candidatos a nomes extraídos: {self.candidates_name}")

    def extract_recipient_address(self):
        """Extrai candidatos a endereços usando NER. Não valida ou faz fuzzy matching."""
        text_clean = normalize_full(self.text)
        self.logger.debug(f"extract_recpient_address() -> Pipeline de normalização full concluído: {text_clean}")
        text_clean = sanitize_edges(text_clean)         # 2️⃣ Limpa bordas do texto
        self.logger.debug(f"extract_recpient_address() -> Bordas sanitizadas: {text_clean}")
        text_clean = sanitize_full(text_clean, clear_cep=True)
        self.logger.debug(f"extract_recpient_address() -> Pipeline de sanitização full concluído: {text_clean}")

        doc = self.nlp_address(text_clean)
        candidates = {"STREET": set(), "NUMBER": set(), "COMPLEMENT": set(), "CITY": set(), "STATE": set()}

        for ent in doc.ents:
            if ent.label_ in candidates:
                cleaned = sanitize_full(ent.text, stop_words=[], min_words=1, for_ner=False)
                if cleaned:
                    candidates[ent.label_].add(cleaned)

        self.__candidates_address = candidates
        self.logger.info(f"Candidatos a endereços extraídos: {self.candidates_address}")

    def extract_apartment_and_block(self) -> dict:
        """
        Extrai número de apartamento e bloco a partir dos candidatos de endereço.
        Busca em todos os labels extraídos.
        Retorna dict com as chaves 'apartment' e 'block' (podem estar vazias).
        """
        apartment = None
        block = None

        apt_pattern = re.compile(r'\b(?:ap|apt|apartamento)\s*(\d{1,4})\b', re.IGNORECASE)
        block_pattern = re.compile(r'\b(?:bloco|bl|blc)\s*([A-Z0-9]{1,3})\b', re.IGNORECASE)

        for label, texts in self.__candidates_address.items():
            for text in texts:
                if not apartment:
                    apt_match = apt_pattern.search(text)
                    if apt_match:
                        apartment = apt_match.group(1)
                        self.logger.debug(f"Apartamento detectado em {label}: {apartment}")

                if not block:
                    block_match = block_pattern.search(text)
                    if block_match:
                        block = block_match.group(1)
                        self.logger.debug(f"Bloco detectado em {label}: {block}")

                if apartment and block:
                    break

        result = {"apartment": apartment, "block": block}

        if not apartment and not block:
            self.logger.info("Nenhum bloco ou apartamento identificado no endereço extraído.")
        else:
            self.logger.info(f"Unidade identificada: {result}")

        return result

    def __str__(self):
        return (
            f"OCR: {self.text}\n"
            f"Candidatos a Name: {self.candidates_name}\n"
            f"Candidatos a Address: {self.candidates_address}\n"
        )
