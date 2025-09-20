from src.sticker import Sticker
from src.utils.normalize import normalize_full
from src.utils.sanitize import sanitize_full, sanitize_name_cand
from rapidfuzz import process, fuzz
import spacy
from pathlib import Path
from itertools import product

class Extractor(Sticker):

    # Lista de moradores para teste (apenas para fuzzy matching)
    TEST_MORADORES = [
        "Mauricio de Souza",
        "Leonardo Sampaio",
        "Jonas Moraes",
        "João Dias",
        "Maria Oliveira",
        "Ruan Rodrigues Da Silva",
        "Ana dos Anjos",
        "Ana Aguiar Moraes",
        "Pedro Henrique Parizoti Meyer",
        "Miguel Savio Pereira de Castro",
        "Sarah Oliveira"
    ]

    TEST_ADDRESSES = [
        "Rua Ana 35 Vila Maria Helena Carapicuiba SP",
        "Avenida Brigadeiro Luis Antonio 1272 Apartamento 16 Sao Paulo SP",
        "Rua Iara 476 Parque dos Camargos Barueri SP",
        "Rua Dos Pregos 476 Condomino Ipe Apartamento 701 Sao Paulo SP",
        "Rua XV de Novembro 500 Bloco 2 Apartamento 12 Jardim Gabriela Jandira SP",
        "Avenida Das Flores 1011 Bloco B Apartamento 715 Centro Varginha MG",
        "Rua Jonas Fonseca 2501 Condominio Marrom Apartamento 404 Sao Goncalo RJ"
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
        - Para candidatos curtos, compara apenas com primeiro ou último nome
        """

        # --- Pipeline completo de limpeza ---
        text_clean = normalize_full(text=self.text, for_address=False)
        text_clean = sanitize_full(text=text_clean,remove_acc=False)
        print(f"Sanitize Pipeline: {text_clean}")
        
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

        # --- Se NER não encontrar nada, tentar sem acentos ---
        if not candidates:
            print("[INFO] NER não encontrou nomes com acentos, tentando sem acentos...")
            combined_lines_no_acc = [sanitize_full(line, remove_acc=True) for line in combined_lines]
            for line in combined_lines_no_acc:
                doc = self.nlp_name(line)
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        candidates.append(ent.text)
            candidates = list(set(candidates))

        print("\n[DEBUG] Candidatos detectados pelo NER:")
        for c in candidates:
            print("   🧍", c)

        # --- Limpeza e filtragem ---
        filtered_candidates = []
        for c in candidates:
            cleaned = sanitize_name_cand(c)
            if cleaned:
                filtered_candidates.append(cleaned)

        # --- Preparar lista de moradores para fuzzy ---
        residents_clean = [r.lower() for r in self.TEST_MORADORES]
        residents_first = [r.split()[0].lower() for r in self.TEST_MORADORES]  # para nomes curtos
        residents_last = [r.split()[-1].lower() for r in self.TEST_MORADORES]

        print("\n[DEBUG] Candidatos no Fuzzy matching:")
        # --- Fuzzy matching ---
        best_candidate, best_match, best_score = None, None, 0
        for cand in filtered_candidates:
            cand_clean = cand.lower()
            cand_tokens = cand_clean.split()
            print("   🧍", cand_clean)
            if len(cand_tokens) == 1 or len(cand_clean) <= 5:
                # nome curto: fuzzy apenas com primeiro ou último nome
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
                # nome longo: fuzzy normalmente com o nome completo
                match = process.extractOne(cand_clean, residents_clean, scorer=fuzz.token_set_ratio)
                if match and match[1] > best_score:
                    best_candidate = cand
                    best_match = self.TEST_MORADORES[residents_clean.index(match[0])]
                    best_score = match[1]

        # --- Definir o nome final ---
        if best_match and best_score >= 70:
            self.__recipient_name = best_match
            print(f"[INFO] Nome final detectado pelo Name NER + Fuzzy: {self.__recipient_name}")
        elif not self.__recipient_name:
            print("[INFO] NER não encontrou nomes, tentando fuzzy no texto completo...")
            text_for_fuzzy = sanitize_full(self.text, min_words=3, for_ner=True, remove_acc=True)
            text_for_fuzzy = sanitize_name_cand(text_for_fuzzy).lower()
            match = process.extractOne(text_for_fuzzy, [r.lower() for r in self.TEST_MORADORES], scorer=fuzz.token_set_ratio)
            if match and match[1] >= 60:
                idx = [r.lower() for r in self.TEST_MORADORES].index(match[0])
                self.__recipient_name = self.TEST_MORADORES[idx]
                print(f"[INFO] Nome detectado pelo fallback fuzzy: {self.__recipient_name}")
            else:
                self.__recipient_name = ""
                print("[INFO] Nenhum nome reconhecido mesmo no fallback")


    def extract_recipient_address(self):
        """
        Extrai endereço do destinatário usando modelo NER específico.
        """
        text_clean = normalize_full(self.text)
        text_clean = sanitize_full(text_clean, clear_cep=True)
        print(f"Sanitize Pipeline: {text_clean}")
        doc = self.nlp_address(text_clean)

        candidates = [ent.text for ent in doc.ents if ent.label_ in ("STREET", "NUMBER", "COMPLEMENT", "CITY", "STATE")]
        full_address_candidate = " ".join(candidates)

        print("\n[DEBUG] Candidatos de endereço detectados pelo NER:")
        for c in candidates:
            print("   🏠", c)

        candidates_by_type = { "STREET": [], "NUMBER": [], "COMPLEMENT": [], "CITY": [], "STATE": [] }

        for ent in doc.ents:
            if ent.label_ in candidates_by_type:
                cleaned = sanitize_full(ent.text, stop_words=[], min_words=1, for_ner=False)
                if cleaned:
                    candidates_by_type[ent.label_].append(cleaned)

        # Gerar combinações plausíveis
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
            match = process.extractOne(
                candidate_str.lower(),
                [a.lower() for a in self.TEST_ADDRESSES],
                scorer=fuzz.token_set_ratio
            )
            if match and match[1] > best_score:
                best_candidate = self.TEST_ADDRESSES[[a.lower() for a in self.TEST_ADDRESSES].index(match[0])]
                best_score = match[1]

        # --- decidir no final ---
        if best_candidate and best_score >= 70:
            self.__recipient_address = best_candidate
            print(f"[INFO] Endereço final detectado pelo Name NER + Fuzzy: {self.__recipient_address}")
        else:
            self.__recipient_address = ""  # sem fallback cru
            print("[INFO] Nenhum endereço válido encontrado")


    def __str__(self):
        return (
            f"OCR: {self.text}\n"
            f"Name : {self.recipient_name}\n"
            f"Address: {self.recipient_address}\n"
        )   