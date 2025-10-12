import unicodedata, re
from src.utils.config_loader import load_stop_words, load_stop_name_tokens
from src.utils.normalize import normalize_numbers
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Lista de siglas de estados brasileiros
STATE_ABBR = {
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
}

def sanitize_name_cand(candidate: str, stop_tokens: set[str] | None = None) -> str:
    """Sanitiza um candidato a nome, removendo stop tokens, números e romanos."""
    from src.utils.utils import is_roman

    if stop_tokens is None:
        stop_tokens = load_stop_name_tokens()

    stop_lower = {t.lower() for t in stop_tokens}
    tokens = candidate.split()
    cleaned_tokens = []

    for t in tokens:
        t_lower = t.lower()
        if t_lower in stop_lower:
            logger.debug(f"Removido stop token: '{t}'")
            continue
        if t.isdigit():
            logger.debug(f"Removido número: '{t}'")
            continue
        if is_roman(t):
            logger.debug(f"Removido número romano: '{t}'")
            continue
        cleaned_tokens.append(t)

    result = " ".join(cleaned_tokens)
    logger.debug(f"sanitize_name_cand: '{candidate}' -> '{result}'")
    return result


def remove_stop_words(text: str, stop_words=None) -> str:
    if stop_words is None:
        stop_words = load_stop_words()
    original = text
    for word in stop_words:
        text = re.sub(rf"\b{word}\w*\b", "", text, flags=re.IGNORECASE)
    logger.debug(f"remove_stop_words: '{original}' -> '{text}'")
    return text


def keep_relevant_chars(text: str, for_ner: bool) -> str:
    original = text
    text = re.sub(r"[^a-zA-Z0-9á-úÁ-ÚçÇ.,\s]", " ", text)
    if for_ner:
        text = re.sub(r"[.,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    logger.debug(f"keep_relevant_chars: '{original}' -> '{text}'")
    return text


def remove_alphanum_codes(text: str) -> str:
    original = text
    text = re.sub(r'\b(?=\w*[A-Za-z])(?=\w*\d)\w{9,}\b', '', text)
    logger.debug(f"remove_alphanum_codes: '{original}' -> '{text}'")
    return text


def remove_long_numbers(text: str, max_len: int = 7) -> str:
    original = text
    text = re.sub(r'\b\d{%d,}\b' % max_len, '', text)
    logger.debug(f"remove_long_numbers: '{original}' -> '{text}'")
    return text


def remove_short_words(words: list[str], min_len: int = 3) -> list[str]:
    from src.utils.utils import is_roman
    out = []
    for w in words:
        if len(w) >= min_len or re.fullmatch(r'\d+', w) or is_roman(w) or w.upper() in STATE_ABBR:
            out.append(w)
        else:
            logger.debug(f"Removida palavra curta: '{w}'")
    return out


def remove_links(words: list[str]) -> list[str]:
    out = [w for w in words if not re.match(r'\w+\.\w+(\.\w+)?', w)]
    removed = set(words) - set(out)
    for w in removed:
        logger.debug(f"Removido link: '{w}'")
    return out


def clear_ceps(text: str) -> str:
    original = text
    text = re.sub(r'\b\d{8}\b', '', text)
    logger.debug(f"clear_ceps: '{original}' -> '{text}'")
    return text


def remove_accents(text: str) -> str:
    original = text
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    logger.debug(f"remove_accents: '{original}' -> '{text}'")
    return text


def remove_codes(text: str, min_len: int = 3) -> str:
    original = text
    text = re.sub(r'\b(?=\w*[A-Za-z])(?=\w*\d)\w{' + str(min_len) + r',}\b', '', text)
    logger.debug(f"remove_codes: '{original}' -> '{text}'")
    return text


def sanitize_full(text: str, stop_words=None, min_words=2, for_ner=True, clear_cep=False, remove_acc=True):
    """Executa pipeline completo de sanitização para OCR."""
    if stop_words is None:
        stop_words = load_stop_words()

    if not text:
        return ""

    logger.debug(f"Pipeline de sanitização iniciado: '{text}'")

    text = remove_stop_words(text, stop_words)
    text = keep_relevant_chars(text, for_ner)
    text = remove_alphanum_codes(text)
    text = normalize_numbers(text)
    text = remove_long_numbers(text)
    text = remove_codes(text)
    if remove_acc:
        text = remove_accents(text)

    words = text.split()
    words = remove_short_words(words, min_len=3)
    words = remove_links(words)
    text = " ".join(words)

    if clear_cep:
        text = clear_ceps(text)

    if len(text.split()) < min_words:
        logger.debug(f"Pipeline de sanitização resultou em texto vazio ou pequeno: '{text}'")
        return ""

    logger.debug(f"Pipeline de sanitização concluído: '{text}'")
    return text
