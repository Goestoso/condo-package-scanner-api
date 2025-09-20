import unicodedata, re
from src.utils.config_loader import STOP_WORDS, STOP_NAME_TOKENS
from src.utils.normalize import normalize_numbers

# Lista de siglas de estados brasileiros
STATE_ABBR = {
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
}

def sanitize_name_cand(candidate: str) -> str:
    """
    Sanitiza um candidato a nome:
      - remove números
      - remove números romanos
      - remove stop tokens
    """
    from src.utils.utils import is_roman
    stop_lower = [t.lower() for t in STOP_NAME_TOKENS]
    tokens = candidate.split()
    cleaned_tokens = []

    for t in tokens:
        t_lower = t.lower()
        if t_lower in stop_lower:
            continue
        if t.isdigit():
            continue
        if is_roman(t):
            continue
        cleaned_tokens.append(t)

    return " ".join(cleaned_tokens)


def remove_stop_words(text: str, stop_words: list[str]) -> str:
    for word in stop_words:
        # \b garante palavra inteira
        text = re.sub(rf"\b{word}\w*\b", "", text, flags=re.IGNORECASE)
    return text

def keep_relevant_chars(text: str, for_ner: bool) -> str:
    text = re.sub(r"[^a-zA-Z0-9á-úÁ-ÚçÇ.,\s]", " ", text)
    if for_ner:
        text = re.sub(r"[.,]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def remove_alphanum_codes(text: str) -> str:
    """
    Remove apenas códigos alfanuméricos LONGOS (prováveis protocolos/chaves).
    Mantém coisas curtas como AP12, BL2, CJ5.
    Critério: token com letras+digitos e comprimento >= 9 -> remover.
    """
    return re.sub(r'\b(?=\w*[A-Za-z])(?=\w*\d)\w{9,}\b', '', text)

def remove_long_numbers(text: str, max_len: int = 7) -> str:
    # Remove números muito longos (ex: CNPJs, protocolos)
    return re.sub(r'\b\d{%d,}\b' % max_len, '', text)

def remove_short_words(words: list[str], min_len: int = 3) -> list[str]:
    from src.utils.utils import is_roman
    """
    Mantém:
      - palavras com comprimento >= min_len
      - tokens puramente numéricos (ex: '2', '12')
      - números romanos válidos
      - siglas de estados brasileiros
    """
    out = []
    for w in words:
        if len(w) >= min_len:
            out.append(w)
            continue
        if re.fullmatch(r'\d+', w):
            out.append(w)
            continue
        if is_roman(w):
            out.append(w)
            continue
        if w.upper() in STATE_ABBR:  # <<< preserva estados
            out.append(w.upper())
            continue
        # caso contrário, descarta
    return out

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

def remove_codes(text: str, min_len: int = 3) -> str:
    """
    Remove tokens alfanuméricos longos (letras + dígitos misturados) que provavelmente
    são códigos/protocolos.
    """
    return re.sub(r'\b(?=\w*[A-Za-z])(?=\w*\d)\w{' + str(min_len) + r',}\b', '', text)



def sanitize_full(text: str, stop_words=STOP_WORDS, min_words=2, for_ner=True, clear_cep=False, remove_acc=True) -> str:
    if not text:
        return ""

    if stop_words is None:
        stop_words = []

    text = remove_stop_words(text, stop_words)
    text = keep_relevant_chars(text, for_ner)
    text = remove_alphanum_codes(text)
    text = normalize_numbers(text)
    text = remove_long_numbers(text)
    text = remove_codes(text)
    if remove_acc: text = remove_accents(text)
    words = text.split()
    words = remove_short_words(words, min_len=3)
    words = remove_links(words)

    text = " ".join(words)

    if clear_cep:
        text = clear_ceps(text)

    if len(text.split()) < min_words:
        return ""

    return text