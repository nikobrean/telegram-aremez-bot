import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOCALES_DIR = BASE_DIR / "locales"

TRANSLATIONS: dict[str, dict] = {}

for p in LOCALES_DIR.glob("*.json"):
    with open(p, "r", encoding="utf-8") as f:
        TRANSLATIONS[p.stem] = json.load(f)

if "en" not in TRANSLATIONS:
    raise RuntimeError("Missing locales/en.json")

def t(lang: str, key: str, **kwargs) -> str:
    lang_dict = TRANSLATIONS.get(lang) or TRANSLATIONS["en"]
    text = lang_dict.get(key) or TRANSLATIONS["en"].get(key) or key
    return text.format(**kwargs)
