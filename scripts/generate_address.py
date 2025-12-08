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
NUM_TOTAL = 10000
TRAIN_RATIO = 0.9
NEGATIVE_RATIO = 0.1  # proporção de exemplos sem endereço
DATA_DIR = Path(__file__).parent.parent / "data"
CITY_FILE = DATA_DIR / "cities.csv"
DATA_DIR.mkdir(exist_ok=True)
TRAIN_JSON = DATA_DIR / "address_training.json"
DEV_JSON = DATA_DIR / "address_dev.json"
TRAIN_SPACY = DATA_DIR / "address_training.spacy"
DEV_SPACY = DATA_DIR / "address_dev.spacy"

ADDRESS_PREFIXES = [
    "Rua", "R.", "Avenida", "Av.", "Rodovia", "Rod.",
    "Estrada", "Travessa", "Trav.", "Praça", "Prç.",
    "Alameda", "Al.", "Viela", "Vl.", "Via"
]

COMPLEMENTS = {
    "ap": ["Apto {num}", "Ap. {num}", "Apartamento {num}", "apt {num}", "ap {num}", "apto {num}"],
    "bloco": ["Bloco {letter}", "Bl. {letter}", "bloco {letter}", "bl {letter}"],
    "torre": ["Torre {num}", "Tr. {num}", "tr {num}", "tr. {num}"],
    "condominio": ["Condomínio {name}", "Cond. {name}", "condominio {name}", "cond {name}", "cond. {name}"],
    "edificio": ["Edifício {name}", "Ed. {name}"]
}

with open(DATA_DIR / "extra_words.json", "r", encoding="utf-8") as f:
    EXTRA_WORDS = json.load(f)

with open(DATA_DIR / "cond_names.json", "r", encoding="utf-8") as f:
    COND_NAMES = json.load(f)

with open(DATA_DIR / "neighborhoods.json", "r", encoding="utf-8") as f:
    COMMON_NEIGHBORHOODS = json.load(f)

# --- Cidade/Estado ---
city_state_map = {}
with open(CITY_FILE, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")
    for row in reader:
        city = row["MUNICÍPIO - IBGE"].strip()
        state = row["UF"].strip()
        city_state_map[city] = state
CITIES = list(city_state_map.keys())

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

def generate_city_state():
    city = random.choice(CITIES)
    state = city_state_map[city]
    return city, state

def generate_neighborhood():
    template = random.choice(COMMON_NEIGHBORHOODS)
    if "{name}" in template:
        template = template.replace("{name}", faker.first_name())
    if "{vogal}" in template:
        template = template.replace("{vogal}", random.choice("aeiou"))
    if random.random() < 0.3:
        prefix = random.choice(["Bairro", "Bair.", "B.", "bairro"])
        template = f"{prefix} {template}"
    return template

def generate_street_and_number():
    prefix = random.choice(ADDRESS_PREFIXES)
    street_name = faker.street_name()
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
    random.shuffle(parts)
    return " ".join(parts)

def add_extra_words(text, entities):
    if random.random() < 0.3:
        choice = random.choice(["start", "end", "both"])
        def pick_extras():
            n = random.randint(1,3)
            return " ".join(random.sample(EXTRA_WORDS, n))
        if choice in ["start","both"]:
            extra = pick_extras()
            text = extra + " " + text
            entities = [(s+len(extra)+1, e+len(extra)+1, l) for (s,e,l) in entities]
        if choice in ["end","both"]:
            extra = pick_extras()
            text = text + " " + extra
    return text, entities

# --- Exemplos negativos ---
def generate_negative_example():
    text = " ".join(random.sample(EXTRA_WORDS, random.randint(3,8)))
    return text, {"entities": []}

# --- Exemplos positivos ---
def generate_positive_example():
    street, number = generate_street_and_number()
    complement = generate_complement() if random.random() < 0.4 else ""
    city, state = generate_city_state()
    
    street_block = [("STREET", street), ("NUMBER", number)]
    complement_block = [("COMPLEMENT", complement)] if complement else []

    # Bairro só aparece se houver cidade
    neighborhood_block = [("COMPLEMENT", generate_neighborhood())] if random.random() < 0.7 else []

    city_state_block = [("CITY", city), ("STATE", state)]

    # Padrões principais e secundários
    main_patterns = [
        street_block + neighborhood_block + complement_block + city_state_block,
        street_block + complement_block + neighborhood_block + city_state_block
    ]

    secondary_patterns = [
        street_block,
        street_block + complement_block,
        street_block + city_state_block[:1],
        street_block + neighborhood_block + city_state_block[:1],
        street_block + city_state_block,
        city_state_block[-1:] + street_block + neighborhood_block + complement_block + city_state_block[:1],
        city_state_block[:1] + street_block + neighborhood_block + complement_block + city_state_block[-1:]
    ]

    pattern_choices = main_patterns * 7 + secondary_patterns  # 70% main, 30% secondary
    pattern = random.choice(pattern_choices)

    text = ""
    entities = []
    current_idx = 0
    sep = " "
    for label, part in pattern:
        if text:
            text += sep
            current_idx += len(sep)
        text += part
        end = current_idx + len(part)
        if label:
            entities.append((current_idx, end, label))
        current_idx = end

    text, entities = add_extra_words(text, entities)
    return text, {"entities": entities}

# --- Função para converter JSON -> .spacy ---
def json_to_spacy(json_path, output_path):
    nlp = spacy.blank("pt")  # cria modelo vazio para português
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

# --- Gerar dataset ---
examples = []
for _ in range(NUM_TOTAL):
    if random.random() < NEGATIVE_RATIO:
        examples.append(generate_negative_example())
    else:
        examples.append(generate_positive_example())

num_train = int(NUM_TOTAL * TRAIN_RATIO)
train_examples = examples[:num_train]
dev_examples = examples[num_train:]

with open(DATA_DIR / "address_training.json", "w", encoding="utf-8") as f:
    json.dump(train_examples, f, ensure_ascii=False, indent=2)
with open(DATA_DIR / "address_dev.json", "w", encoding="utf-8") as f:
    json.dump(dev_examples, f, ensure_ascii=False, indent=2)
    
# --- Converter os JSONs ---
json_to_spacy(TRAIN_JSON, TRAIN_SPACY)
json_to_spacy(DEV_JSON, DEV_SPACY)

print(f"{len(train_examples)} exemplos de treino e {len(dev_examples)} exemplos de dev gerados.")
