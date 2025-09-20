import re
from rapidfuzz import process, fuzz
import unicodedata
import yaml
from pathlib import Path

# Siglas e nomes oficiais
STATES = {
    "AC": "ACRE", "AL": "ALAGOAS", "AP": "AMAPÁ", "AM": "AMAZONAS",
    "BA": "BAHIA", "CE": "CEARÁ", "DF": "DISTRITO FEDERAL", "ES": "ESPÍRITO SANTO",
    "GO": "GOIÁS", "MA": "MARANHÃO", "MT": "MATO GROSSO", "MS": "MATO GROSSO DO SUL",
    "MG": "MINAS GERAIS", "PA": "PARÁ", "PB": "PARAÍBA", "PR": "PARANÁ",
    "PE": "PERNAMBUCO", "PI": "PIAUÍ", "RJ": "RIO DE JANEIRO", "RN": "RIO GRANDE DO NORTE",
    "RS": "RIO GRANDE DO SUL", "RO": "RONDÔNIA", "RR": "RORAIMA", "SC": "SANTA CATARINA",
    "SP": "SÃO PAULO", "SE": "SERGIPE", "TO": "TOCANTINS"
}

# Stop words irrelevantes
CONFIG_PATH = Path(__file__).parent.parent / "configs" / "sanitize.yml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

STOP_WORDS = config.get("stop_words", [])


def normalize_ceps(txt: str) -> str:
    def cep_replacer(match):
        digits = re.sub(r'\D', '', match.group())
        return digits if len(digits) == 8 else match.group()
    return re.sub(r'\b\d{5}[-\s]?\d{3}\b', cep_replacer, txt)

def normalize_sn(txt: str) -> str:
    return re.sub(r"\b(s[\s\-\/]?n|sem\s+n[úu]mero)\b",
                  "semnumero", txt, flags=re.IGNORECASE)

def normalize_states(text: str) -> str:  # --- Normaliza estados em siglas (ex: São Paulo vira SP) --- 

    def get_fuzzy_states(raw_state:str):   
        if not raw_state:
            return None
        s_clean = raw_state.strip().upper()
        # match exato sigla
        if s_clean in STATES:
            return s_clean
        # match exato nome completo
        for sig, name in STATES.items():
            if s_clean == name.upper():
                return sig
        # fuzzy match
        names = list(STATES.values())
        match, score, idx = process.extractOne(s_clean, names, scorer=fuzz.token_sort_ratio)
        if score >= 75:
            return list(STATES.keys())[idx]
        return None

    # normalizar estados multi-word
    words = text.split()
    i = 0
    while i < len(words):
        matched = False
        # tentar n-grams 3,2,1
        for n in [3, 2, 1]:
            if i + n <= len(words):
                span = " ".join(words[i:i+n])
                norm = get_fuzzy_states(span)
                if norm:
                    words[i:i+n] = [norm]
                    matched = True
                    break
        i += 1 if not matched else 1

    text = " ".join(words)
    return text

def normalize_case(text: str, preserve_upper=None) -> str:
    """
    Capitaliza cada palavra do texto.
    preserve_upper: lista de palavras/siglas que devem permanecer em maiúsculas
    """
    if preserve_upper is None:
        preserve_upper = []
    words = text.split()
    normalized = []
    for w in words:
        if w.upper() in preserve_upper:
            normalized.append(w.upper())
        else:
            normalized.append(w.capitalize())
    return " ".join(normalized)


def remove_stopwords(text: str, stop_words) -> str:
    for sw in stop_words:
        text = re.sub(rf"{re.escape(sw)}\b", "", text, flags=re.IGNORECASE)
    return text

def keep_relevant_chars(text: str, for_ner: bool) -> str:
    text = re.sub(r"[^a-zA-Z0-9á-úÁ-ÚçÇ.,\s]", " ", text)
    if for_ner:
        text = re.sub(r"[.,]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def remove_alphanum_codes(text: str) -> str:
    return re.sub(r'\b\w*\d+\w*\b',
                  lambda m: '' if re.search(r'\D', m.group()) else m.group(),
                  text)

def remove_long_numbers(text: str, max_len: int = 8) -> str:
    return re.sub(rf'\b\d{{{max_len+1},}}\b', '', text)

def remove_short_words(words: list[str], min_len: int = 3) -> list[str]:
    return [w for w in words if len(w) >= min_len]

def remove_links(words: list[str]) -> list[str]:
    return [w for w in words if not re.match(r'\w+\.\w+(\.\w+)?', w)]

def clear_ceps(text: str) -> str:
    return re.sub(r'\b\d{8}\b', '', text)

def remove_accents(text: str) -> str:
    """
    Remove acentos de um texto, transformando 'á' em 'a', 'ç' em 'c', etc.
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def sanitize_full(text: str, stop_words=STOP_WORDS, min_words=2, for_ner=True, clear_cep=False) -> str:
    if not text:
        return ""

    if stop_words is None:
        stop_words = []

    text = remove_stopwords(text, stop_words)
    text = keep_relevant_chars(text, for_ner)
    text = remove_alphanum_codes(text)
    text = remove_long_numbers(text)
    text = remove_accents(text)

    words = text.split()
    words = remove_short_words(words, min_len=3)
    words = remove_links(words)

    text = " ".join(words)

    if clear_cep:
        text = clear_ceps(text)

    if len(text.split()) < min_words:
        return ""

    return text

def find_ceps(text: str):
    return re.findall(r'\b\d{5}-?\d{3}\b', text)

def find_codes(text: str):
    return re.findall(r'\b[a-zA-Z0-9]{9,}\b', text)

def full_pipeline(text: str) -> str:
    """Executa normalização completa de texto para NER."""
    text = normalize_ceps(text)
    text = normalize_states(text)
    text = normalize_sn(text)
    text = normalize_case(text)
    text = sanitize_full(text, clear_cep=True)
    print(f"Full Pipeline: {text}")
    return text