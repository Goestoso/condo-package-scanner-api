from src.condo_package_label import CondoPackageLabel
from src.utils.logger import get_logger
from src.utils.normalize import normalize_full
from src.utils.sanitize import sanitize_full
from pathlib import Path
import spacy

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
        text_clean = sanitize_full(text_clean, remove_acc=False)

        doc = self.nlp_name(text_clean)
        self.__candidates_name = {ent.text for ent in doc.ents if ent.label_ == "PERSON"}

        self.logger.debug(f"Candidatos a nomes extraídos: {self.candidates_name}")

    def extract_recipient_address(self):
        """Extrai candidatos a endereços usando NER. Não valida ou faz fuzzy matching."""
        text_clean = normalize_full(self.text)
        text_clean = sanitize_full(text_clean, clear_cep=True)

        doc = self.nlp_address(text_clean)
        candidates = {"STREET": set(), "NUMBER": set(), "COMPLEMENT": set(), "CITY": set(), "STATE": set()}

        for ent in doc.ents:
            if ent.label_ in candidates:
                cleaned = sanitize_full(ent.text, stop_words=[], min_words=1, for_ner=False)
                if cleaned:
                    candidates[ent.label_].add(cleaned)

        self.__candidates_address = candidates
        self.logger.debug(f"Candidatos a endereços extraídos: {self.candidates_address}")

    def __str__(self):
        return (
            f"OCR: {self.text}\n"
            f"Candidatos a Name: {self.candidates_name}\n"
            f"Candidatos a Address: {self.candidates_address}\n"
        )
