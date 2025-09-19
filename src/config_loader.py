import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "configs" / "extractor.yml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

STOP_NAME_TOKENS = set(config.get("stop_name_tokens", []))