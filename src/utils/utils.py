import re
from src.utils.logger import get_logger
from rapidfuzz import process, fuzz

logger = get_logger(__name__)

ROMAN_PATTERN = r'^(M{0,3})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'

def is_roman(token: str) -> bool:
    """
    Retorna True se o token for um número romano válido.
    Ex: I, II, III, IV, V, IX, X, XII, XX, etc.
    """
    token_up = token.upper()
    result = bool(re.match(ROMAN_PATTERN, token_up))
    logger.debug(f"is_roman: '{token}' -> {result}")
    return result

def find_ceps(text: str):
    ceps = re.findall(r'\b\d{5}-?\d{3}\b', text)
    if ceps:
        logger.debug(f"find_ceps: encontrados {len(ceps)} CEP(s): {ceps}")
    return ceps

def find_codes(text: str):
    codes = re.findall(r'\b[a-zA-Z0-9]{9,}\b', text)
    if codes:
        logger.debug(f"find_codes: encontrados {len(codes)} código(s): {codes}")
    return codes

def fuzzy_compare(candidates:list, name: str, threshold: int = 70) -> list[tuple[str, int]]:
    """
    Compara um nome os nomes do banco usando fuzzy matching.
    Retorna lista de tuplas (nome_do_banco, score) acima do threshold.
    """

    matches = process.extract(
        name,
        candidates,
        scorer=fuzz.token_set_ratio,
        score_cutoff=threshold
    )
    return matches  # [(nome, score), ...]