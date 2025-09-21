import json
import random
import unicodedata
import re
from pathlib import Path
from faker import Faker
import spacy
from spacy.tokens import DocBin
import csv

faker = Faker("pt_BR")

# --- Configurações ---
NUM_TOTAL = 20000
TRAIN_RATIO = 0.9
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

ADDRESS_PREFIXES = [
    "Rua", "R.", "Avenida", "Av.", "Rodovia", "Rod.",
    "Estrada", "Travessa", "Trav.", "Praça", "Prç.",
    "Alameda", "Al.", "Viela", "Vl.", "Via", "Alameda"
]

COMPLEMENTS = {
    "ap": ["Apto {num}", "Ap. {num}", "Apartamento {num}", "apt {num}", "ap {num}", "apto {num}"],
    "bloco": ["Bloco {letter}", "Bl. {letter}", "bloco {letter}", "bl {letter}"],
    "torre": ["Torre {num}", "Tr. {num}", "tr {num}", "tr. {num}"],
    "condominio": ["Condomínio {name}", "Cond. {name}", "condominio {name}", "cond {name}", "cond. {name}"],
    "edificio": ["Edifício {name}", "Ed. {name}"]
}

DATA_DIR = Path(__file__).parent.parent / "data"
CITY_FILE = DATA_DIR / "cities.csv"

with open(DATA_DIR / "extra_words.json", "r", encoding="utf-8") as f:
    EXTRA_WORDS = json.load(f)

with open(DATA_DIR / "cond_names.json", "r", encoding="utf-8") as f:
    COND_NAMES = json.load(f)

LABELS = ["STREET", "NUMBER", "COMPLEMENT", "CITY", "STATE", "NEIGHBORHOOD"]

# --- Funções auxiliares ---
def add_extra_words(text, entities):
    if random.random() < 0.3:  # ~30% das vezes adiciona extras
        choice = random.choice(["start", "end", "both"])

        def pick_extras():
            # escolhe entre 1 e 3 extras
            n = random.randint(1, 3)
            return " ".join(random.sample(EXTRA_WORDS, n))

        if choice in ["start", "both"]:
            extra = pick_extras()
            text = extra + " " + text
            entities = [(s + len(extra) + 1, e + len(extra) + 1, l) for (s, e, l) in entities]

        if choice in ["end", "both"]:
            extra = pick_extras()
            text = text + " " + extra
            # como é no final, não precisa mexer nos índices

    return text, entities

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

with open(DATA_DIR / "neighborhoods.json", "r", encoding="utf-8") as f:
    COMMON_NEIGHBORHOODS = json.load(f)

def generate_neighborhood():
    # escolhe aleatoriamente entre Faker e lista de bairros comuns
    if random.random() < 0.5:
        bairro = faker.bairro()  # Faker
    else:
        bairro = random.choice(COMMON_NEIGHBORHOODS)  # lista comum

    # chance de adicionar o prefixo "Bairro"
    if random.random() < 0.3:
        prefix = random.choice(["Bairro", "Bair.", "B.", "bairro"])
        bairro = f"{prefix} {bairro}"

    return random_case(bairro)


def generate_number():
    r = random.random()
    if r < 0.05:
        return random.choice(["s/n", "S/N", "s-n", "s n", "sem numero", "sem número", "semnumero"])
    elif r < 0.30:
        number = str(random.randint(1, 9999))
        prefix = random.choice(["nº", "N", "Número"])
        return f"{prefix} {number}"
    else:
        return str(random.randint(1, 9999))

# --- Cidade/Estado ---
city_state_map = {}
with open(CITY_FILE, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")
    for row in reader:
        city = row["MUNICÍPIO - IBGE"].strip()
        state = row["UF"].strip()
        city_state_map[city] = state
CITIES = list(city_state_map.keys())

def generate_city_state():
    city = random.choice(CITIES)
    state = city_state_map[city]
    return city, state

# --- Ruído OCR/typo ---
def apply_ocr_noise(text: str, label: str) -> str:
    def random_accent(c):
        mapping = {"a":"á","e":"é","i":"í","o":"ó","u":"ú","c":"ç"}
        return mapping.get(c.lower(), c) if random.random() < 0.1 else c

    if label in ["STREET", "COMPLEMENT", "STATE"]:
        text = "".join([random_accent(c) for c in text])
        if random.random() < 0.5:
            text = random_case(text)
    elif label == "CITY":
        if random.random() < 0.05:
            text = "".join([random_accent(c) for c in text])
            text = random_case(text)
    return text

def apply_typo_noise(text: str) -> str:
    words = text.split()
    new_words = []
    for w in words:
        if len(w) <= 3 or "." in w:
            new_words.append(w)
            continue
        if random.random() < 0.2:
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

def clean_prefix(street_name: str) -> str:
    for prefix in ADDRESS_PREFIXES:
        pattern = rf"^{prefix}\s+"
        street_name = re.sub(pattern, "", street_name, flags=re.IGNORECASE)
    return street_name.strip()

def clean_prepositions(text: str) -> str:
    preps = ["de", "da", "do", "das", "dos"]
    words = text.split()
    cleaned = []
    for i, w in enumerate(words):
        if w.lower() in preps and cleaned and cleaned[-1].lower() in preps:
            cleaned[-1] = w
        else:
            cleaned.append(w)
    return " ".join(cleaned)

def generate_street_and_number():
    forbidden_prefixes = [remove_accents(v.split()[0].lower()) for vals in COMPLEMENTS.values() for v in vals]

    # --- caso especial: gerar rua curta (5% dos casos, ajusta como quiser) ---
    if random.random() < 0.05:
        short_streets = [
            "Ana", "Bela", "Sol", "Céu", "Paz", "Flor",
            "Luz", "Ouro", "Bem", "Um", "Dois"
        ]
        prefix = random.choice(["Rua", "R.", "Av.", "Travessa", "Praça"])
        street_name = random.choice(short_streets)
        number = generate_number()
        return f"{prefix} {street_name}", number

    # --- caso normal (faker) ---
    while True:
        street_name = faker.street_name()
        street_parts = street_name.split()
        normalized_prefixes = [remove_accents(p.lower()) for p in ADDRESS_PREFIXES]
        if remove_accents(street_parts[0].lower()) in normalized_prefixes:
            street_name = " ".join(street_parts[1:])
        street_name = clean_prepositions(street_name)
        first_word = remove_accents(street_name.split()[0].lower())
        if first_word not in forbidden_prefixes:
            break

    prefix = random.choice(ADDRESS_PREFIXES)
    number = generate_number()
    return f"{prefix} {street_name}", number


def generate_complement():
    parts = []
    roll = random.random()
    def random_terreo():
        return random.choice(["Térreo","Terreo","térreo","terreo","TÉRREO","TERREO"])
    if roll < 0.65:
        parts.append(random_terreo() if random.random() < 0.05 else random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1,300)))
    elif roll < 0.9:
        parts.append(random.choice(COMPLEMENTS["bloco"]).format(letter=random.choice("ABCDE")))
        parts.append(random_terreo() if random.random() < 0.05 else random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1,300)))
    else:
        kind = random.choice(["condominio","edificio"])
        parts.append(random.choice(COMPLEMENTS[kind]).format(name=random.choice(COND_NAMES)))
        if random.random() < 0.5:
            parts.append(random.choice(COMPLEMENTS["bloco"]).format(letter=random.choice("ABCDE")))
        parts.append(random_terreo() if random.random() < 0.05 else random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1,300)))
    if len(parts) > 1:
        random.shuffle(parts)
    complement_text = " ".join(parts)
    complement_text = random_case(complement_text)
    complement_text = apply_typo_noise(complement_text)
    return complement_text

def generate_example():
    street, number = generate_street_and_number()
    complement = generate_complement() if random.random() < 0.4 else ""
    city, state = generate_city_state()
    neighborhood_block = [("NEIGHBORHOOD", generate_neighborhood())] if random.random() < 0.7 else []
    street_block = [("STREET", street), ("NUMBER", number)]
    complement_block = [("COMPLEMENT", complement)] if complement else []
    city_state_block = []
    if random.random() > 0.15:
        city_state_block.append(("CITY", city))
    if random.random() > 0.15:
        city_state_block.append(("STATE", state))
    pattern = random.choice([
        street_block + complement_block + neighborhood_block + city_state_block,
        street_block + neighborhood_block + complement_block + city_state_block,
        neighborhood_block + street_block + complement_block + city_state_block,
        city_state_block[:1] + neighborhood_block + street_block + complement_block + city_state_block[1:],
    ])
    text = ""
    entities = []
    current_idx = 0
    sep = " "
    for label, part in pattern:
        if text:
            text += sep
            current_idx += len(sep)
        part_noisy = part
        if label in ["STREET","COMPLEMENT","CITY","STATE","NEIGHBORHOOD"]:
            part_noisy = apply_ocr_noise(part_noisy,label)
            part_noisy = apply_typo_noise(part_noisy)
        text += part_noisy
        end = current_idx + len(part_noisy)
        if label is not None:
            entities.append((current_idx, end, label))
        current_idx = end
    text, entities = add_extra_words(text, entities)
    return text, {"entities": entities}


# --- Gerar dataset ---
examples = [generate_example() for _ in range(NUM_TOTAL)]
num_train = int(NUM_TOTAL * TRAIN_RATIO)
train_examples = examples[:num_train]
dev_examples = examples[num_train:]

with open(OUTPUT_DIR / "address_training.json", "w", encoding="utf-8") as f:
    json.dump(train_examples, f, ensure_ascii=False, indent=2)
with open(OUTPUT_DIR / "address_dev.json", "w", encoding="utf-8") as f:
    json.dump(dev_examples, f, ensure_ascii=False, indent=2)

print(f"{len(train_examples)} exemplos de treino e {len(dev_examples)} exemplos de dev gerados.")

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

json_to_spacy(OUTPUT_DIR / "address_training.json", OUTPUT_DIR / "address_training.spacy")
json_to_spacy(OUTPUT_DIR / "address_dev.json", OUTPUT_DIR / "address_dev.spacy")
