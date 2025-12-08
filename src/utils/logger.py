import yaml
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

CONFIG_FILE = Path(__file__).parent.parent.parent / "configs" / "logger.yml"

# Valores padrão seguros
DEFAULT_CONFIG = {
    "log_file": "logs/condo_package_scanner_api.log",
    "log_level": "DEBUG",
    "console_level": "INFO",
    "max_bytes": 5 * 1024 * 1024,
    "backup_count": 3,
    "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S"
}

def load_logger_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        if not isinstance(cfg, dict):
            print("[WARN] logger.yml inválido. Usando configurações padrão.")
            return DEFAULT_CONFIG
        # Preenche valores ausentes com default
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg or cfg[k] is None:
                print(f"[WARN] logger.yml: '{k}' ausente ou inválido. Usando padrão: {v}")
                cfg[k] = v
        return cfg
    except Exception as e:
        print(f"[WARN] Não foi possível ler logger.yml ({e}). Usando padrão.")
        return DEFAULT_CONFIG

# --- Inicialização do logger ---
def get_logger(name: str) -> logging.Logger:
    cfg = load_logger_config()
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, cfg["log_level"].upper(), logging.DEBUG))

    if not logger.handlers:
        # Rotating file
        Path(cfg["log_file"]).parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            cfg["log_file"],
            maxBytes=cfg["max_bytes"],
            backupCount=cfg["backup_count"],
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, cfg["log_level"].upper(), logging.DEBUG))

        # Console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, cfg["console_level"].upper(), logging.INFO))

        formatter = logging.Formatter(fmt=cfg["format"], datefmt=cfg["datefmt"])
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def close_logger(logger: logging.Logger):
    for h in logger.handlers[:]:
        h.close()
        logger.removeHandler(h)