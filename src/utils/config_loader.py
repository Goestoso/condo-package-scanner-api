import yaml
import json
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.parent / "configs"
DATA_SANITIZE_DIR = Path(__file__).parent.parent.parent / "data" / "sanitize"


# --- BANCO DE DADOS ---
def load_db_config() -> dict:
    path = CONFIG_DIR / "db_connection.yml"
    if not path.exists():
        logger.error(f"Arquivo de conexão não encontrado: {path}")
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --- STOP TOKENS (para nomes, NER) ---
def load_stop_name_tokens() -> set:
    """Carrega tokens de nomes a serem ignorados no NER (stop_name_tokens.txt)."""
    path = DATA_SANITIZE_DIR / "stop_name_tokens.txt"
    if not path.exists():
        logger.warning(f"Arquivo de stop_name_tokens não encontrado: {path}")
        return set()

    try:
        with open(path, "r", encoding="utf-8") as f:
            tokens = {line.strip().lower() for line in f if line.strip()}
        logger.debug(f"{len(tokens)} stop name tokens carregados.")
        return tokens
    except Exception as e:
        logger.warning(f"Falha ao carregar stop_name_tokens.txt: {e}")
        return set()


# --- STOP WORDS (para limpeza geral do texto OCR) ---
def load_stop_words() -> list:
    """Carrega stop words genéricas (stop_words.txt)."""
    path = DATA_SANITIZE_DIR / "stop_words.txt"
    if not path.exists():
        logger.warning(f"Arquivo de stop_words não encontrado: {path}")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            words = [line.strip().lower() for line in f if line.strip()]
        logger.debug(f"{len(words)} stop words carregadas.")
        return words
    except Exception as e:
        logger.warning(f"Falha ao carregar stop_words.txt: {e}")
        return []


# --- NORMALIZE / PREFIXOS E COMPLEMENTOS ---
def load_normalize_config() -> tuple[dict, dict]:
    path = CONFIG_DIR / "normalize.json"
    if not path.exists():
        logger.warning(f"Arquivo de normalização não encontrado: {path}")
        return {}, {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("complements", {}), cfg.get("prefixes", {})
    except Exception as e:
        logger.warning(f"Falha ao carregar normalize.json: {e}")
        return {}, {}
