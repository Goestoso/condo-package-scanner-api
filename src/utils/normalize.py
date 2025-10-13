import re
import unicodedata
from rapidfuzz import process, fuzz
import src.utils.config_loader as config_loader
from src.utils.logger import get_logger

logger = get_logger(__name__)

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

def normalize_name(name: str) -> str:
    """Normaliza um nome: remove acentos e ajusta capitalização."""
    if not name:
        return ""
    name_clean = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    # Capitaliza cada palavra
    name_clean = ' '.join(word.capitalize() for word in name_clean.split())
    return name_clean

def normalize_address_complement(text: str) -> str:
    """Substitui abreviações de complementos por palavras completas."""
    COMPLEMENTS = config_loader.load_normalize_config()[0]  # só os complements
    words = text.split()
    for i, w in enumerate(words):
        key = w.lower().rstrip(".")
        if key in COMPLEMENTS:
            logger.debug(f"Substituindo complemento '{w}' por '{COMPLEMENTS[key]}'")
            words[i] = COMPLEMENTS[key]
    return " ".join(words)

def normalize_block(block: str | None) -> str | None:
    """
    Normaliza o bloco, convertendo números em letras.
    Exemplo: 1 → A, 2 → B, 3 → C, etc.
    """
    if not block:
        return None

    block = str(block).strip().upper()

    # Mapeamento básico de número → letra
    mapping = {
        "1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "6": "F",
        "7": "G", "8": "H", "9": "I", "10": "J"
    }

    # Se for um número válido, converte
    if block in mapping:
        return mapping[block]

    # Se já for letra, normaliza (ex: "bloco a" → "A")
    for prefix in ["BLOCO", "BL", "B"]:
        if block.startswith(prefix):
            block = block.replace(prefix, "").strip()
            break

    # Mantém só a letra, se for o caso
    if len(block) == 1 and block.isalpha():
        return block.upper()

    return block


def normalize_address_prefix(text: str) -> str:
    """Normaliza prefixos de logradouro usando fuzzy match."""
    PREFIXES = config_loader.load_normalize_config()[1]  # só os prefixes
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
        if best_score >= 70:
            logger.debug(f"Prefixo '{w}' normalizado para '{best_match}' (score={best_score})")
            words[i] = best_match
    return " ".join(words)

def normalize_ceps(txt: str) -> str:
    """Normaliza CEPs, removendo traços e espaços indevidos."""
    def cep_replacer(match):
        digits = re.sub(r'\D', '', match.group())
        if len(digits) == 8:
            logger.debug(f"CEP '{match.group()}' normalizado para '{digits}'")
            return digits
        else:
            logger.debug(f"CEP '{match.group()}' ignorado (inválido)")
            return match.group()
    return re.sub(r'\b\d{5}[-\s]?\d{3}\b', cep_replacer, txt)

def normalize_sn(txt: str) -> str:
    """Substitui 's/n' e variantes por 'semnumero'."""
    def replacer(match):
        logger.debug(f"Substituindo '{match.group()}' por 'semnumero'")
        return "semnumero"
    return re.sub(r"\b(s[\s\-\/]?n|sem\s+n[úu]mero)\b", replacer, txt, flags=re.IGNORECASE)

def normalize_states(text: str) -> str:
    """Normaliza nomes de estados para suas siglas usando fuzzy match se necessário."""

    def get_fuzzy_states(raw_state: str):
        if not raw_state:
            return None
        s_clean = raw_state.strip().upper()
        if s_clean in STATES:
            logger.debug(f"Estado '{raw_state}' já é sigla")
            return s_clean
        for sig, name in STATES.items():
            if s_clean == name.upper():
                logger.debug(f"Estado '{raw_state}' normalizado para sigla '{sig}'")
                return sig
        names = list(STATES.values())
        match, score, idx = process.extractOne(s_clean, names, scorer=fuzz.token_sort_ratio)
        if score >= 75:
            logger.debug(f"Estado '{raw_state}' fuzzy match -> '{list(STATES.keys())[idx]}' (score={score})")
            return list(STATES.keys())[idx]
        logger.debug(f"Estado '{raw_state}' não pôde ser normalizado")
        return None

    words = text.split()
    i = 0
    while i < len(words):
        matched = False
        for n in [3, 2, 1]:
            if i + n <= len(words):
                span = " ".join(words[i:i+n])
                norm = get_fuzzy_states(span)
                if norm:
                    words[i:i+n] = [norm]
                    matched = True
                    break
        i += 1 if not matched else 1
    return " ".join(words)

def normalize_case(text: str, preserve_upper=None) -> str:
    """Capitaliza palavras, preservando certas siglas."""
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
    """Remove espaços entre dígitos."""
    result = re.sub(r'(\d)\s+(?=\d)', r'\1', text)
    if result != text:
        logger.debug(f"Números normalizados: '{text}' -> '{result}'")
    return result

def normalize_full(text: str, for_address=True) -> str:
    """Executa pipeline completo de normalização para NER."""
    logger.debug(f"Pipeline de normalização iniciado: '{text}'")
    if for_address:
        text = normalize_states(text)
        text = normalize_sn(text)
        text = normalize_address_prefix(text)
        text = normalize_address_complement(text)
    text = normalize_ceps(text)
    text = normalize_case(text)
    text = normalize_numbers(text)
    logger.debug(f"Pipeline de normalização concluído: '{text}'")
    return text
