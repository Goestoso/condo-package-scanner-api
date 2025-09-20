import yaml
from pathlib import Path
import json

CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "extractor.yml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

STOP_NAME_TOKENS = set(config.get("stop_name_tokens", []))

# Stop words irrelevantes
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "sanitize.yml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

STOP_WORDS = config.get("stop_words", [])

# --- carregar arquivo de normalização ---
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "normalize.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    normalize_config = json.load(f)

COMPLEMENTS = normalize_config.get("complements", {})
PREFIXES = normalize_config.get("prefixes", {})