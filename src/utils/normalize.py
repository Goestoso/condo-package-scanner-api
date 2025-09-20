import re
from rapidfuzz import process, fuzz
from src.utils.config_loader import COMPLEMENTS, PREFIXES


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

def normalize_address_complement(text: str) -> str:
    """Substitui abreviações de complementos por palavras completas."""
    words = text.split()
    for i, w in enumerate(words):
        key = w.lower().rstrip(".")
        if key in COMPLEMENTS:
            words[i] = COMPLEMENTS[key]
    return " ".join(words)

def normalize_address_prefix(text: str) -> str:
    """Normaliza prefixos de logradouro usando fuzzy match."""
    words = text.split()
    for i, w in enumerate(words):
        w_lower = w.lower()
        best_match = None
        best_score = 0
        for prefix, variations in PREFIXES.items():
            match, score, _ = process.extractOne(w_lower, variations, scorer=fuzz.ratio)
            if score > best_score:
                best_score = score
                best_match = prefix
        if best_score >= 70:  # limiar razoável
            words[i] = best_match
    return " ".join(words)

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

def normalize_numbers(text: str) -> str:
    """
    Junta todos os dígitos que estão separados apenas por espaço.
    Ex: '1 1' -> '11', '123 456 789' -> '123456789'
    """
    return re.sub(r'(\d)\s+(?=\d)', r'\1', text)

def normalize_full(text: str, for_address = True) -> str:
    """Executa normalização completa de texto para NER."""
    if for_address:
        text = normalize_states(text)
        text = normalize_sn(text)
        text = normalize_address_prefix(text)
        text = normalize_address_complement(text)
    text = normalize_ceps(text)
    text = normalize_case(text)
    print(f"Normalize Pipeline: {text}")
    return text