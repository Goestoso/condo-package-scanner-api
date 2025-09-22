import yaml, json
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)  # Cria um logger para este módulo

CONFIG_DIR = Path(__file__).parent.parent.parent / "configs"

# --- Carregar extractor.yml ---
EXTRACTOR_CONFIG_FILE = CONFIG_DIR / "extractor.yml"
try:
    with open(EXTRACTOR_CONFIG_FILE, encoding="utf-8") as f:
        EXTRACTOR_CONFIG = yaml.safe_load(f)
    STOP_NAME_TOKENS = set(EXTRACTOR_CONFIG.get("stop_name_tokens", []))
    logger.info(f"Config 'extractor.yml' carregada com sucesso. Tokens de parada: {len(STOP_NAME_TOKENS)}")
except Exception as e:
    logger.warning(f"Falha ao carregar 'extractor.yml': {e}")
    STOP_NAME_TOKENS = set()

# --- Carregar sanitize.yml ---
SANITIZE_CONFIG_FILE = CONFIG_DIR / "sanitize.yml"
try:
    with open(SANITIZE_CONFIG_FILE, encoding="utf-8") as f:
        SANITIZE_CONFIG = yaml.safe_load(f)
    STOP_WORDS = SANITIZE_CONFIG.get("stop_words", [])
    logger.info(f"Config 'sanitize.yml' carregada com sucesso. Stop words: {len(STOP_WORDS)}")
except Exception as e:
    logger.warning(f"Falha ao carregar 'sanitize.yml': {e}")
    STOP_WORDS = []

# --- Carregar normalize.json ---
NORMALIZE_CONFIG_FILE = CONFIG_DIR / "normalize.json"
try:
    with open(NORMALIZE_CONFIG_FILE, encoding="utf-8") as f:
        NORMALIZE_CONFIG = json.load(f)
    COMPLEMENTS = NORMALIZE_CONFIG.get("complements", {})
    PREFIXES = NORMALIZE_CONFIG.get("prefixes", {})
    logger.info(f"Config 'normalize.json' carregada com sucesso. Complements: {len(COMPLEMENTS)}, Prefixes: {len(PREFIXES)}")
except Exception as e:
    logger.warning(f"Falha ao carregar 'normalize.json': {e}")
    COMPLEMENTS = {}
    PREFIXES = {}
