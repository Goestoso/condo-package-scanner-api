from src.sticker import Sticker
from rapidfuzz import process, fuzz
import spacy, src.utils as utils, src.config_loader as config_loader
from pathlib import Path

class Extractor(Sticker):

    # Lista de moradores para teste (apenas para fuzzy matching)
    TEST_MORADORES = [
        "Maurício de Souza",
        "João Dias",
        "Maria Oliveira",
        "Ruan Rodrigues Da Silva",
        "Ana dos Anjos",
        "Ana Aguiar Moraes",
        "Pedro Henrique Parizoti Meyer",
        "Miguel Sávio Pereira de Castro",
    ]

    TEST_ADDRESSES = [
        "Rua Ana 35 Vila Maria Helena Carapicuiba SP",
        "Avenida Brigadeiro Luis Antonio 1272 São Paulo SP",
        "Rua Iara 476 Parque dos Camargos Barueri SP"
    ]

    __MODEL_NAME_PATH = Path(__file__).parent.parent / "models" / "name_ner" / "model-last"

    __MODEL_ADDRESS_PATH = Path(__file__).parent.parent / "models" / "address_ner" / "model-last"

    def __init__(self, img:str):
        super().__init__(img)
        self.__recipient_name = ""  # atributo para guardar o nome do morador
        self.__recipient_address = "" # atributo para guardar o endereço do morador
        
        # carregar modelos
        self.nlp_name = spacy.load(self.__MODEL_NAME_PATH)
        self.nlp_address = spacy.load(self.__MODEL_ADDRESS_PATH)

    @property
    def recipient_name(self):
        return self.__recipient_name
    
    @property
    def recipient_address(self):
        return self.__recipient_address
    
    def extract_recipient_name(self):
        """
        Extrai o nome do destinatário usando:
        1. NER para detectar candidatos
        2. Fuzzy matching para mapear candidatos aos nomes reais
        """

        # --- Pipeline completo de limpeza ---
        text_clean = utils.full_pipeline(self.text)
        
        # Quebrar em linhas
        useful_lines = text_clean.splitlines()

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

        # --- Rodar NER ---
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

        print("\n[DEBUG] Candidatos detectados pelo NER:")
        for c in candidates:
            print("   🧍", c)

        # --- Pré-filtrar candidatos ---
        filtered_candidates = []
        for c in candidates:
            tokens = [t for t in c.split() if t.lower() not in config_loader.STOP_NAME_TOKENS]
            cleaned = " ".join(tokens)
            cleaned = cleaned.strip()
            # somente candidatos plausíveis: 2-6 palavras, sem números
            if 1 < len(cleaned.split()) <= 6 and not any(ch.isdigit() for ch in cleaned):
                filtered_candidates.append(cleaned)

        # --- Preparar lista de moradores para fuzzy ---
        residents_clean = [r.lower() for r in self.TEST_MORADORES]

        # --- Fuzzy matching ---
        best_candidate, best_match, best_score = None, None, 0
        for cand in filtered_candidates:
            cand_clean = cand.lower()
            # Primeiro tentar match exato
            if cand_clean in residents_clean:
                idx = residents_clean.index(cand_clean)
                best_candidate = cand
                best_match = self.TEST_MORADORES[idx]
                best_score = 100
                break  # match exato encontrado, não precisa de fuzzy
            # Senão, fuzzy
            match = process.extractOne(
                cand_clean,
                residents_clean,
                scorer=fuzz.token_sort_ratio
            )
            if match and match[1] > best_score:
                best_candidate = cand
                best_match = self.TEST_MORADORES[residents_clean.index(match[0])]
                best_score = match[1]

        # --- Definir o nome final ---
        if best_match and best_score >= 70:
            self.__recipient_name = best_match
            print(f"[INFO] Nome final detectado pelo Fuzzy: {self.__recipient_name}")
        else:
            # fallback
            self.__recipient_name = best_candidate if best_candidate else ""
            print(f"[INFO] Fallback nome detectado: {self.__recipient_name}")


    def extract_recipient_address(self):
        """
        Extrai endereço do destinatário usando modelo NER específico.
        """
        text_clean = utils.full_pipeline(self.text)
        doc = self.nlp_address(text_clean)

        candidates = [ent.text for ent in doc.ents if ent.label_ in ("STREET", "NUMBER", "COMPLEMENT", "CITY", "STATE")]
        full_address_candidate = " ".join(candidates)

        print("\n[DEBUG] Candidatos de endereço detectados pelo NER:")
        for c in candidates:
            print("   🏠", c)

        best_candidate, best_score = None, 0

        for cand in candidates:
            match = process.extractOne(
                cand,
                self.TEST_ADDRESSES,
                scorer=fuzz.token_set_ratio
            )
            if match and match[1] > best_score:
                best_candidate = match[0]
                best_score = match[1]

        self.__recipient_address = best_candidate if best_candidate else full_address_candidate

    def __str__(self):
        return (
            f"OCR: {self.text}\n"
            f"Name : {self.recipient_name}\n"
            f"Address: {self.recipient_address}\n"
        )   