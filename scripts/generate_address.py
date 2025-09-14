import json
import random
import unicodedata
from pathlib import Path
from faker import Faker
import spacy
from spacy.tokens import DocBin

faker = Faker("pt_BR")

# --- Configurações ---
NUM_TOTAL = 10000          # total de exemplos
TRAIN_RATIO = 0.9          # proporção de treino
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

ADDRESS_PREFIXES = [
    "Rua", "R.", "Avenida", "Av.", "Rodovia", "Rod.",
    "Estrada", "Travessa", "Trav.", "Praça", "Prç.",
    "Alameda", "Al.", "Viela", "Vl."
]

COMPLEMENTS = [
    "Apto {num}", "Ap. {num}", "Apartamento {num}", "apt {num}", "ap {num}", "apto {num}",
    "Bloco {letter}", "Bl. {letter}", "bloco {letter}", "bl {letter}",
    "Torre {num}", "Tr. {num}", "tr {num}", "tr. {num}",
    "Condomínio {name}", "Cond. {name}", "condominio {name}", "cond {name}", "cond. {name}",
    "Edifício {name}", "Ed. {name}"
]

COND_NAMES = [
    "Jardim das Flores", "Parque Verde", "Solar das Águas",
    "Residencial Bela Vista", "Morada do Sol", "Alvorada",
    "Polaris", "Green Valley", "Spazio", "Ipê", "Living"
]

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
    comps = [random.choice(COMPLEMENTS)]
    if random.random() < 0.3:
        comps.append(random.choice(COMPLEMENTS))
    return ", ".join(c.format(
        num=random.randint(1, 200),
        letter=random.choice("ABCDE"),
        name=random.choice(COND_NAMES)
    ) for c in comps)

def generate_cep():
    cep = faker.postcode()
    if random.random() < 0.5:
        cep = cep.replace("-", "")
    return cep

def generate_number():
    if random.random() < 0.05:
        return "s/n"
    return str(random.randint(1, 9999))

def generate_example():
    prefix = random.choice(ADDRESS_PREFIXES)
    street = faker.street_name()
    number = generate_number()
    city = faker.city()
    state = faker.estado_sigla()
    cep = generate_cep()
    complement = ""
    if random.random() < 0.4:
        complement = generate_complement()

    parts = [f"{prefix} {street}", number, complement, city, state, cep]
    sep = ", " if random.random() < 0.7 else " "
    text = sep.join([p for p in parts if p])

    # Ruído aleatório
    if random.random() < 0.1:
        text += f" {random.randint(1000, 9999)}"

    # Maiúsculas/minúsculas ou remover acentos
    if random.random() < 0.2:
        text = remove_accents(text)
    elif random.random() < 0.4:
        text = random_case(text)

    # Calcular offsets
    entities = []
    current_idx = 0
    for part, label in zip(parts, LABELS):
        if not part:
            continue
        start = text.find(part, current_idx)
        if start != -1:
            end = start + len(part)
            entities.append((start, end, label))
            current_idx = end

    return (text, {"entities": entities})

# --- Gerar dataset completo ---
examples = [generate_example() for _ in range(NUM_TOTAL)]

# --- Separar treino e dev ---
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
