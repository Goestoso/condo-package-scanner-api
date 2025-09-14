import json
import random
import unicodedata
import re
from pathlib import Path
from faker import Faker
import spacy
from spacy.tokens import DocBin

faker = Faker("pt_BR")

# --- Configurações ---
NUM_TOTAL = 10000
TRAIN_RATIO = 0.9
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

ADDRESS_PREFIXES = [
    "Rua", "R.", "Avenida", "Av.", "Rodovia", "Rod.",
    "Estrada", "Travessa", "Trav.", "Praça", "Prç.",
    "Alameda", "Al.", "Viela", "Vl."
]

COMPLEMENTS = {
    "ap": ["Apto {num}", "Ap. {num}", "Apartamento {num}", "apt {num}", "ap {num}", "apto {num}"],
    "bloco": ["Bloco {letter}", "Bl. {letter}", "bloco {letter}", "bl {letter}"],
    "torre": ["Torre {num}", "Tr. {num}", "tr {num}", "tr. {num}"],
    "condominio": ["Condomínio {name}", "Cond. {name}", "condominio {name}", "cond {name}", "cond. {name}"],
    "edificio": ["Edifício {name}", "Ed. {name}"]
}

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "extra_words.json", "r", encoding="utf-8") as f:
    EXTRA_WORDS = json.load(f)

with open(DATA_DIR / "cond_names.json", "r", encoding="utf-8") as f:
    COND_NAMES = json.load(f)

LABELS = ["STREET", "NUMBER", "COMPLEMENT", "CITY", "STATE", "CEP"]

# --- Funções auxiliares ---
def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def random_case(text):
    r = random.random()
    if r < 0.33:
        return text.lower()
    elif r < 0.66:
        return text.upper()
    else:
        return text.title()

def generate_complement():
    roll = random.random()
    parts = []

    if roll < 0.7:
        parts.append(random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1, 300)))
    elif roll < 0.9:
        parts.append(random.choice(COMPLEMENTS["bloco"]).format(letter=random.choice("ABCDE")))
        parts.append(random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1, 300)))
    else:
        kind = random.choice(["condominio", "edificio"])
        parts.append(random.choice(COMPLEMENTS[kind]).format(name=random.choice(COND_NAMES)))
        if random.random() < 0.5:
            parts.append(random.choice(COMPLEMENTS["bloco"]).format(letter=random.choice("ABCDE")))
        parts.append(random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1, 300)))

    return " ".join(parts)

def generate_number():
    if random.random() < 0.05:
        variants = ["s/n", "S/N", "s-n", "s n", "sem numero", "sem número", "semnumero"]
        return random.choice(variants)
    return str(random.randint(1, 9999))

def generate_cep():
    cep = faker.postcode()
    cep = re.sub(r'\D', '', cep)
    return cep.zfill(8)

def generate_city_state():
    city = faker.city()
    if city in ["Rio de Janeiro", "São Paulo"]:
        state = random.choice(["RJ", "Rio de Janeiro"]) if city == "Rio de Janeiro" else random.choice(["SP", "São Paulo"])
    else:
        state = random.choice([faker.estado_sigla(), faker.state()])  # UF ou nome do estado
    return city, state

def apply_ocr_noise(text: str, label: str) -> str:
    r = random.random()
    # Aplica ruído OCR aleatório em campos de texto
    if label in ["STREET", "COMPLEMENT", "CITY", "STATE"] and r < 0.3:  # 30% das vezes
        # Separar letras de siglas
        text = re.sub(r"\b([A-Z]{2})\b", lambda m: " ".join(m.group()), text)
    # Acentos aleatórios e random case
    def random_accent(c):
        mapping = {"a":"á","e":"é","i":"í","o":"ó","u":"ú","c":"ç"}
        return mapping.get(c.lower(), c) if random.random() < 0.1 else c
    text = "".join([random_accent(c) for c in text])
    if random.random() < 0.5:
        text = random_case(text)
    return text

import unicodedata

def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def generate_street():
    # Lista de prefixos já normalizada
    normalized_prefixes = [remove_accents(p.lower()) for p in ADDRESS_PREFIXES]

    if random.random() < 0.5:
        # Usar o nome completo do Faker
        street = faker.street_name()
    else:
        # Usar nosso prefixo + nome do Faker sem o prefixo
        street_name = faker.street_name()
        street_parts = street_name.split()
        # Remover prefixo do Faker se já existir na lista de prefixos
        if remove_accents(street_parts[0].lower()) in normalized_prefixes:
            street_name_clean = " ".join(street_parts[1:])
        else:
            street_name_clean = street_name
        # Escolher prefixo aleatório que não seja igual ao do Faker
        while True:
            prefix = random.choice(ADDRESS_PREFIXES)
            if remove_accents(prefix.lower()) != remove_accents(street_parts[0].lower()):
                break
        street = f"{prefix} {street_name_clean}"

    return street


def generate_example():
    prefix = random.choice(ADDRESS_PREFIXES)
    street = faker.street_name()
    number = generate_number()
    complement = generate_complement() if random.random() < 0.4 else ""
    city, state = generate_city_state()
    cep = generate_cep()

    base_parts = [f"{prefix} {street}", number]
    labels = ["STREET", "NUMBER"]

    if complement:
        base_parts.append(complement)
        labels.append("COMPLEMENT")

    base_parts.extend([city, state, cep])
    labels.extend(["CITY", "STATE", "CEP"])

    # Inserir palavras extras só no começo ou fim
    n_extra = random.randint(0, 2)
    extras = [f"{random.choice(EXTRA_WORDS)} {faker.name()}" for _ in range(n_extra)]
    position = random.choice(["start", "end"])
    if position == "start":
        base_parts = extras + base_parts
        labels = [None]*n_extra + labels
    elif position == "end":
        base_parts = base_parts + extras
        labels = labels + [None]*n_extra

    # Construir texto final e calcular offsets
    sep = " "
    text = ""
    entities = []
    current_idx = 0
    for p, lbl in zip(base_parts, labels):
        if text:
            text += sep
            current_idx += len(sep)
        start = current_idx
        # Aplicar ruído OCR se lbl existe
        p_noisy = apply_ocr_noise(p, lbl) if lbl else p
        text += p_noisy
        end = start + len(p_noisy)
        if lbl is not None:
            entities.append((start, end, lbl))
        current_idx = end

    return text, {"entities": entities}

# --- Gerar dataset completo ---
examples = [generate_example() for _ in range(NUM_TOTAL)]
num_train = int(NUM_TOTAL * TRAIN_RATIO)
train_examples = examples[:num_train]
dev_examples = examples[num_train:]

# --- Salvar JSON ---
train_json_path = OUTPUT_DIR / "address_training.json"
dev_json_path = OUTPUT_DIR / "address_dev.json"

with open(train_json_path, "w", encoding="utf-8") as f:
    json.dump(train_examples, f, ensure_ascii=False, indent=2)
with open(dev_json_path, "w", encoding="utf-8") as f:
    json.dump(dev_examples, f, ensure_ascii=False, indent=2)

print(f"{len(train_examples)} exemplos de treino e {len(dev_examples)} exemplos de dev gerados.")

# --- Converter para .spacy ---
def json_to_spacy(json_path, output_path):
    nlp = spacy.blank("pt")
    db = DocBin()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for text, annot in data:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annot.get("entities", []):
            span = doc.char_span(start, end, label=label)
            if span is not None:
                ents.append(span)
        doc.ents = ents
        db.add(doc)
    db.to_disk(output_path)
    print(f"{output_path} criado com sucesso!")

json_to_spacy(train_json_path, OUTPUT_DIR / "address_training.spacy")
json_to_spacy(dev_json_path, OUTPUT_DIR / "address_dev.spacy")
