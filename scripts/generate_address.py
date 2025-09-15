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
    "Alameda", "Al.", "Viela", "Vl.", "Via", ""
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

LABELS = ["STREET", "NUMBER", "COMPLEMENT", "CITY", "STATE"]

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
    """
    Gera complementos de endereço com:
    - Capitalização aleatória
    - Ordem aleatória de blocos (apartamento, torre, bloco, condomínio/edifício)
    - Ruído de digitação
    """
    parts = []

    roll = random.random()
    
    # Decidir o tipo de complemento
    if roll < 0.7:
        # Apenas apartamento
        parts.append(random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1, 300)))
    elif roll < 0.9:
        # Bloco + apartamento
        parts.append(random.choice(COMPLEMENTS["bloco"]).format(letter=random.choice("ABCDE")))
        parts.append(random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1, 300)))
    else:
        # Condomínio/Edifício possivelmente com bloco e apartamento
        kind = random.choice(["condominio", "edificio"])
        parts.append(random.choice(COMPLEMENTS[kind]).format(name=random.choice(COND_NAMES)))
        if random.random() < 0.5:
            parts.append(random.choice(COMPLEMENTS["bloco"]).format(letter=random.choice("ABCDE")))
        parts.append(random.choice(COMPLEMENTS["ap"]).format(num=random.randint(1, 300)))

    # Aleatorizar a ordem dos blocos
    if len(parts) > 1:
        random.shuffle(parts)

    # Juntar partes e aplicar capitalização aleatória
    complement_text = " ".join(parts)
    complement_text = random_case(complement_text)

    # Aplicar ruído de digitação
    complement_text = apply_typo_noise(complement_text)

    return complement_text


def generate_number():
    r = random.random()
    # ~5% sem número
    if r < 0.05:
        variants = ["s/n", "S/N", "s-n", "s n", "sem numero", "sem número", "semnumero"]
        return random.choice(variants)
    # ~25% número com prefixo
    elif r < 0.30:
        number = str(random.randint(1, 9999))
        prefix = random.choice(["nº", "N", "Número"])
        return f"{prefix} {number}"
    # ~70% só o número
    else:
        return str(random.randint(1, 9999))


def generate_city_state():
    city = faker.city()
    state = faker.estado_sigla()  # UF ou nome do estado
    return city, state

def apply_ocr_noise(text: str, label: str) -> str:
    # Aplica ruído OCR aleatório em campos de texto
    if label in ["STREET", "COMPLEMENT", "CITY", "STATE"]:
        # apenas acentos aleatórios e random case
        def random_accent(c):
            mapping = {"a":"á","e":"é","i":"í","o":"ó","u":"ú","c":"ç"}
            return mapping.get(c.lower(), c) if random.random() < 0.1 else c
        text = "".join([random_accent(c) for c in text])
        if random.random() < 0.5:
            text = random_case(text)
    return text


def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def clean_prefix(street_name: str) -> str:
    # Remove prefixos duplicados (ignora case e acento)
    for prefix in ADDRESS_PREFIXES:
        pattern = rf"^{prefix}\s+"  # só se for no começo
        street_name = re.sub(pattern, "", street_name, flags=re.IGNORECASE)
    return street_name.strip()

def generate_street_and_number():
    # Criar lista de palavras proibidas (prefixos de complementos)
    forbidden_prefixes = []
    for vals in COMPLEMENTS.values():
        for v in vals:
            # Pega a primeira palavra de cada template (antes do {num} ou {name})
            first_word = v.split()[0]
            forbidden_prefixes.append(remove_accents(first_word.lower()))

    while True:
        street_name = faker.street_name()
        # remove prefixo duplicado do Faker
        street_parts = street_name.split()
        normalized_prefixes = [remove_accents(p.lower()) for p in ADDRESS_PREFIXES]
        if remove_accents(street_parts[0].lower()) in normalized_prefixes:
            street_name = " ".join(street_parts[1:])

        # Limpar duplicações de preposições
        street_name = clean_prepositions(street_name)

        # Verifica se não começa com palavra de complemento
        first_word = remove_accents(street_name.split()[0].lower())
        if first_word not in forbidden_prefixes:
            break  # nome válido

    # Escolher prefixo
    prefix = random.choice(ADDRESS_PREFIXES)
    number = generate_number()

    return f"{prefix} {street_name}", number


def clean_prepositions(text: str) -> str:
    """
    Remove duplicações estranhas de preposições.
    Ex.: 'de da', 'do da', 'de dos' -> mantêm apenas a última.
    """
    # Lista de preposições mais comuns em nomes de ruas
    preps = ["de", "da", "do", "das", "dos"]
    
    words = text.split()
    cleaned = []
    for i, w in enumerate(words):
        if w.lower() in preps:
            # Se o anterior também era prep, ignora o anterior
            if cleaned and cleaned[-1].lower() in preps:
                cleaned[-1] = w  # substitui pelo atual
            else:
                cleaned.append(w)
        else:
            cleaned.append(w)
    return " ".join(cleaned)

def apply_typo_noise(text: str) -> str:
    """
    Aplica ruído de digitação em palavras completas (não abreviações).
    """
    words = text.split()
    new_words = []
    
    for w in words:
        # não mexer em abreviações (curtas, com ponto, ou maiúsculas isoladas)
        if len(w) <= 3 or "." in w:
            new_words.append(w)
            continue

        if random.random() < 0.2:  # 20% chance de aplicar erro
            typo_type = random.choice(["remove", "insert", "swap"])

            if typo_type == "remove" and len(w) > 4:
                idx = random.randint(1, len(w)-2)  # não remove primeira/última
                w = w[:idx] + w[idx+1:]

            elif typo_type == "insert":
                idx = random.randint(1, len(w)-1)
                random_char = random.choice("aeiou")
                w = w[:idx] + random_char + w[idx:]

            elif typo_type == "swap" and len(w) > 4:
                idx = random.randint(1, len(w)-2)
                w = (w[:idx] + w[idx+1] + w[idx] + 
                     w[idx+2:])

        new_words.append(w)

    return " ".join(new_words)

# --- Inserir palavras extras/ruído no começo e no final ---
def insert_noise(base_parts, labels, max_extra=2, noise_chance=0.3):
    """
    base_parts: lista de strings (STREET, NUMBER, etc)
    labels: lista de labels correspondentes
    max_extra: número máximo de palavras extras
    noise_chance: chance de adicionar ruído em começo/fim
    """
    n_start = random.randint(0, max_extra) if random.random() < noise_chance else 0
    n_end = random.randint(0, max_extra) if random.random() < noise_chance else 0

    start_extras = [f"{random.choice(EXTRA_WORDS)} {faker.name()}" for _ in range(n_start)]
    end_extras = [f"{random.choice(EXTRA_WORDS)} {faker.name()}" for _ in range(n_end)]

    if start_extras:
        base_parts = start_extras + base_parts
        labels = [None]*n_start + labels
    if end_extras:
        base_parts = base_parts + end_extras
        labels = labels + [None]*n_end

    return base_parts, labels

def generate_example():
    # --- Gerar partes do endereço ---
    street, number = generate_street_and_number()
    complement = generate_complement() if random.random() < 0.4 else ""
    city, state = generate_city_state()

    # --- Construir blocos com labels ---
    street_block = [("STREET", street), ("NUMBER", number)]
    complement_block = [("COMPLEMENT", complement)] if complement else []
    city_state_block = [("CITY", city), ("STATE", state)]

    # --- Escolher variação de ordem ---
    pattern = random.choice([
        street_block + city_state_block + complement_block,
        city_state_block + street_block + complement_block,
        complement_block + street_block + city_state_block,
        city_state_block[::-1] + street_block + complement_block,  # state + city + street + number
    ])

    # --- Inserir palavras extras aleatórias no início ou fim ---
    n_extra = random.randint(0, 2)
    extras = [(None, f"{random.choice(EXTRA_WORDS)} {faker.name()}") for _ in range(n_extra)]
    position = random.choice(["start", "end"])
    if extras:
        if position == "start":
            pattern = extras + pattern
        else:
            pattern = pattern + extras

    # --- Construir texto final e calcular offsets ---
    text = ""
    entities = []
    current_idx = 0
    sep = " "
    for label, part in pattern:
        if text:
            text += sep
            current_idx += len(sep)
        start = current_idx
        # Aplicar ruído OCR e typo se label existe
        part_noisy = part
        if label in ["STREET", "COMPLEMENT", "CITY", "STATE"]:
            part_noisy = apply_ocr_noise(part_noisy, label)
            part_noisy = apply_typo_noise(part_noisy)
        text += part_noisy
        end = start + len(part_noisy)
        if label is not None:
            entities.append((start, end, label))
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
