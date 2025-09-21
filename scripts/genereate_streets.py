import json
import random
from pathlib import Path
from faker import Faker
import spacy
from spacy.tokens import DocBin

faker = Faker("pt_BR")
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

ADDRESS_PREFIXES = [
    "Rua", "R.", "Avenida", "Av.", "Rodovia", "Rod.",
    "Estrada", "Travessa", "Trav.", "Praça", "Prç.",
    "Alameda", "Al.", "Viela", "Vl.", "Via"
]

NUM_EXAMPLES = 50  # Dataset curto

# --- Carregar extra_words.json ---
with open(OUTPUT_DIR / "extra_words.json", "r", encoding="utf-8") as f:
    EXTRA_WORDS = json.load(f)

# --- Funções de ruído ---
def apply_typo_noise(text: str) -> str:
    words = text.split()
    new_words = []
    for w in words:
        if len(w) <= 3 or "." in w:
            new_words.append(w)
            continue
        if random.random() < 0.5:
            typo_type = random.choice(["remove", "insert", "swap"])
            if typo_type == "remove" and len(w) > 4:
                idx = random.randint(1, len(w)-2)
                w = w[:idx] + w[idx+1:]
            elif typo_type == "insert":
                idx = random.randint(1, len(w)-1)
                random_char = random.choice("aeiou")
                w = w[:idx] + random_char + w[idx:]
            elif typo_type == "swap" and len(w) > 4:
                idx = random.randint(1, len(w)-2)
                w = w[:idx] + w[idx+1] + w[idx] + w[idx+2:]
        new_words.append(w)
    return " ".join(new_words)

def random_case(text):
    r = random.random()
    if r < 0.33:
        return text.lower()
    elif r < 0.66:
        return text.upper()
    else:
        return text.title()

def apply_ocr_noise(text):
    mapping = {"a":"á","e":"é","i":"í","o":"ó","u":"ú","c":"ç"}
    noisy = "".join([mapping.get(c.lower(), c) if random.random()<0.1 else c for c in text])
    if random.random() < 0.5:
        noisy = random_case(noisy)
    return noisy

def add_extra_words(text, entities):
    # adiciona palavras extras antes/depois
    if random.random() < 0.8:
        n_before = random.randint(1, 5)
        n_after = random.randint(1, 5)
        extras_before = " ".join(random.sample(EXTRA_WORDS, n_before))
        extras_after = " ".join(random.sample(EXTRA_WORDS, n_after))
        new_entities = []
        for start, end, label in entities:
            new_entities.append((start + len(extras_before) + 1, end + len(extras_before) + 1, label))
        text = f"{extras_before} {text} {extras_after}"
        return text, new_entities
    return text, entities

# --- Gerar Mauro variations ---
def generate_mauro_variations():
    base = [
        "Rua dos Pregos 476",
        "R. dos Pregos 476",
        "Rua Dos Pregos 476",
        "Rua dos Pregos n°476",
        "Rua dos Pregos nº 476"
    ]
    examples = []
    for name in base:
        for _ in range(3):  # 3 variações cada
            text = apply_ocr_noise(name)
            text = apply_typo_noise(text)
            space_idx = text.rfind(" ")
            street_span = (0, space_idx)
            number_span = (space_idx + 1, len(text))
            entities = [
                (street_span[0], street_span[1], "STREET"),
                (number_span[0], number_span[1], "NUMBER")
            ]
            text, entities = add_extra_words(text, entities)
            examples.append((text, {"entities": entities}))
    return examples

# --- Gerar exemplos Faker ---
def generate_faker_examples(n):
    examples = []
    for _ in range(n):
        prefix = random.choice(ADDRESS_PREFIXES)
        street_name = faker.street_name()
        number = str(random.randint(1, 9999))
        text = f"{prefix} {street_name} {number}"
        text_noisy = apply_ocr_noise(text)
        text_noisy = apply_typo_noise(text_noisy)
        street_span = (0, len(prefix) + 1 + len(street_name))
        number_span = (len(prefix) + 1 + len(street_name) + 1, len(text_noisy))
        entities = [
            (street_span[0], street_span[1], "STREET"),
            (number_span[0], number_span[1], "NUMBER")
        ]
        text_noisy, entities = add_extra_words(text_noisy, entities)
        examples.append((text_noisy, {"entities": entities}))
    return examples

# --- Montar dataset ---
faker_examples = generate_faker_examples(NUM_EXAMPLES - 5)
mauro_examples = generate_mauro_variations()
examples = faker_examples + mauro_examples
random.shuffle(examples)

# --- Salvar JSON ---
with open(OUTPUT_DIR / "street_training.json", "w", encoding="utf-8") as f:
    json.dump(examples, f, ensure_ascii=False, indent=2)

# --- Converter para .spacy ---
def json_to_spacy(json_path, output_path):
    nlp = spacy.blank("pt")
    db = DocBin()
    discarded = 0
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for text, annot in data:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annot.get("entities", []):
            span = doc.char_span(start, end, label=label)
            if span is not None:
                ents.append(span)
            else:
                discarded += 1
        doc.ents = ents
        db.add(doc)
    db.to_disk(output_path)
    print(f"{output_path} criado com sucesso! {discarded} spans descartados.")

json_to_spacy(OUTPUT_DIR / "street_training.json", OUTPUT_DIR / "street_training.spacy")
