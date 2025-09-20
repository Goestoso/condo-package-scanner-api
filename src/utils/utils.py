import re

ROMAN_PATTERN = r'^(M{0,3})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'

def is_roman(token: str) -> bool:
    """
    Retorna True se o token for um número romano válido.
    Ex: I, II, III, IV, V, IX, X, XII, XX, etc.
    """
    token = token.upper()
    return bool(re.match(ROMAN_PATTERN, token))

def find_ceps(text: str):
    return re.findall(r'\b\d{5}-?\d{3}\b', text)

def find_codes(text: str):
    return re.findall(r'\b[a-zA-Z0-9]{9,}\b', text)