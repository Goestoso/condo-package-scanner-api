from src.sticker import Sticker
from src.utils.logger import get_logger
from src.utils.normalize import normalize_full
from src.utils.sanitize import sanitize_full, sanitize_name_cand
from rapidfuzz import process, fuzz
import spacy
from pathlib import Path
from itertools import product

class Extractor(Sticker):

    TEST_MORADORES = [
        "Mauricio de Souza", "Leonardo Sampaio", "Jonas Moraes", 
        "João Dias", "Maria Oliveira", "Ruan Rodrigues Da Silva",
        "Ana dos Anjos", "Ana Aguiar Moraes", "Pedro Henrique Parizoti Meyer",
        "Miguel Savio Pereira de Castro", "Sarah Oliveira"
    ]

    TEST_ADDRESSES = [
        "Rua Ana 35 Vila Maria Helena Carapicuiba SP",
        "Rua Ana 35 Carapicuiba SP",
        "Avenida Brigadeiro Luis Antonio 1272 Apartamento 16 Sao Paulo SP",
        "Rua Iara 476 Parque dos Camargos Barueri SP",
        "Rua Dos Pregos 476 Condomino Ipe Apartamento 701 Sao Paulo SP",
        "Rua XV de Novembro 500 Bloco 2 Apartamento 12 Jardim Gabriela Jandira SP",
        "Avenida Das Flores 1011 Bloco B Apartamento 715 Centro Varginha MG",
        "Avenida Das Flores",
        "Rua Jonas Fonseca 2501 Condominio Marrom Apartamento 404 Sao Goncalo RJ"
    ]

    __MODEL_NAME_PATH = Path(__file__).parent.parent / "models" / "name_ner" / "model-last"
    __MODEL_ADDRESS_PATH = Path(__file__).parent.parent / "models" / "address_ner" / "model-last"

    def __init__(self, img:str):
        super().__init__(img)
        self.logger = get_logger(self.__class__.__name__)
        self.__recipient_name = ""
        self.__recipient_address = ""
        
        self.logger.info("Carregando modelos NER...")
        self.nlp_name = spacy.load(self.__MODEL_NAME_PATH)
        self.nlp_address = spacy.load(self.__MODEL_ADDRESS_PATH)
        self.logger.info("Modelos carregados com sucesso.")

    @property
    def recipient_name(self):
        return self.__recipient_name
    
    @property
    def recipient_address(self):
        return self.__recipient_address

    def extract_recipient_name(self):
        self.logger.debug("Iniciando extração do nome do destinatário...")
        text_clean = normalize_full(text=self.text, for_address=False)
        text_clean = sanitize_full(text=text_clean, remove_acc=False)
        self.logger.debug(f"Pipeline de sanitização concluído: {text_clean}")

        useful_lines = text_clean.splitlines()
        combined_lines = []
        buffer = ""
        for line in useful_lines:
            buffer = f"{buffer} {line}".strip() if buffer else line
            if len(buffer.split()) >= 3:
                combined_lines.append(buffer)
                buffer = ""
        if buffer:
            combined_lines.append(buffer)

        candidates = []
        doc_full = self.nlp_name("\n".join(combined_lines))
        for ent in doc_full.ents:
            if ent.label_ == "PERSON":
                candidates.append(ent.text)

        for line in combined_lines:
            doc = self.nlp_name(line)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    candidates.append(ent.text)

        candidates = list(set(candidates))
        if not candidates:
            self.logger.info("NER não encontrou nomes com acentos, tentando sem acentos...")
            combined_lines_no_acc = [sanitize_full(line, remove_acc=True) for line in combined_lines]
            for line in combined_lines_no_acc:
                doc = self.nlp_name(line)
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        candidates.append(ent.text)
            candidates = list(set(candidates))

        self.logger.debug(f"Candidatos detectados pelo NER: {candidates}")

        filtered_candidates = [sanitize_name_cand(c) for c in candidates if sanitize_name_cand(c)]
        self.logger.debug(f"Candidatos após sanitização: {filtered_candidates}")

        residents_clean = [r.lower() for r in self.TEST_MORADORES]
        residents_first = [r.split()[0].lower() for r in self.TEST_MORADORES]
        residents_last = [r.split()[-1].lower() for r in self.TEST_MORADORES]

        best_candidate, best_match, best_score = None, None, 0
        for cand in filtered_candidates:
            cand_clean = cand.lower()
            cand_tokens = cand_clean.split()
            if len(cand_tokens) == 1 or len(cand_clean) <= 5:
                match_first = process.extractOne(cand_tokens[0], residents_first, scorer=fuzz.token_set_ratio)
                match_last = process.extractOne(cand_tokens[0], residents_last, scorer=fuzz.token_set_ratio)
                if match_first and match_first[1] > best_score:
                    idx = residents_first.index(match_first[0])
                    best_candidate = cand
                    best_match = self.TEST_MORADORES[idx]
                    best_score = match_first[1]
                if match_last and match_last[1] > best_score:
                    idx = residents_last.index(match_last[0])
                    best_candidate = cand
                    best_match = self.TEST_MORADORES[idx]
                    best_score = match_last[1]
            else:
                match = process.extractOne(cand_clean, residents_clean, scorer=fuzz.token_set_ratio)
                if match and match[1] > best_score:
                    best_candidate = cand
                    best_match = self.TEST_MORADORES[residents_clean.index(match[0])]
                    best_score = match[1]

        if best_match and best_score >= 70:
            self.__recipient_name = best_match
            self.logger.info(f"Nome final detectado: {self.__recipient_name}")
        else:
            self.__recipient_name = ""
            self.logger.info("Nenhum nome reconhecido")

    def extract_recipient_address(self):
        self.logger.debug("Iniciando extração de endereço...")
        text_clean = normalize_full(self.text)
        text_clean = sanitize_full(text_clean, clear_cep=True)
        self.logger.debug(f"Pipeline de sanitização de endereço: {text_clean}")

        doc = self.nlp_address(text_clean)
        candidates_by_type = { "STREET": [], "NUMBER": [], "COMPLEMENT": [], "CITY": [], "STATE": [] }

        for ent in doc.ents:
            if ent.label_ in candidates_by_type:
                cleaned = sanitize_full(ent.text, stop_words=[], min_words=1, for_ner=False)
                if cleaned:
                    candidates_by_type[ent.label_].append(cleaned)

        self.logger.debug(f"Candidatos por tipo: {candidates_by_type}")

        all_combinations = list(product(
            candidates_by_type["STREET"] or [""],
            candidates_by_type["NUMBER"] or [""],
            candidates_by_type["COMPLEMENT"] or [""],
            candidates_by_type["CITY"] or [""],
            candidates_by_type["STATE"] or [""]
        ))

        best_candidate, best_score = None, 0
        for comb in all_combinations:
            candidate_str = " ".join([c for c in comb if c])
            match = process.extractOne(candidate_str.lower(), [a.lower() for a in self.TEST_ADDRESSES], scorer=fuzz.token_set_ratio)
            if match and match[1] > best_score:
                best_candidate = self.TEST_ADDRESSES[[a.lower() for a in self.TEST_ADDRESSES].index(match[0])]
                best_score = match[1]

        if best_candidate and best_score >= 70:
            self.__recipient_address = best_candidate
            self.logger.info(f"Endereço final detectado: {self.__recipient_address}")
        else:
            self.__recipient_address = ""
            self.logger.info("Nenhum endereço válido encontrado")

    def __str__(self):
        return (
            f"OCR: {self.text}\n"
            f"Name : {self.recipient_name}\n"
            f"Address: {self.recipient_address}\n"
        )
