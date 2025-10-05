import yaml, json
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)  # Cria um logger para este módulo

CONFIG_DIR = Path(__file__).parent.parent.parent / "configs"

def load_db_config() -> dict:
    path = CONFIG_DIR / "db_connection.yml"
    if not path.exists():
        logger.error(f"Arquivo de conexão não encontrado: {path}")
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_extractor_config() -> set:
    path = CONFIG_DIR / "extractor.yml"
    try:
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return set(cfg.get("stop_name_tokens", []))
    except Exception as e:
        logger.warning(f"Falha ao carregar 'extractor.yml': {e}")
        return set()

def load_sanitize_config() -> list:
    path = CONFIG_DIR / "sanitize.yml"
    try:
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("stop_words", [])
    except Exception as e:
        logger.warning(f"Falha ao carregar 'sanitize.yml': {e}")
        return []

def load_normalize_config() -> tuple[dict, dict]:
    path = CONFIG_DIR / "normalize.json"
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("complements", {}), cfg.get("prefixes", {})
    except Exception as e:
        logger.warning(f"Falha ao carregar 'normalize.json': {e}")
        return {}, {}
