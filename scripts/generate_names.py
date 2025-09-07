import json
import random
import unicodedata
from pathlib import Path
from faker import Faker

faker = Faker("pt_BR")

# --- Extrair base de nomes e sobrenomes ---
first_names = set()
last_names = set()
for _ in range(5000):
    name = faker.name().split()
    if len(name) >= 2:
        first_names.add(name[0])
        last_names.add(name[-1])

first_names = list(first_names)
last_names = list(last_names)
print(f"Coletados {len(first_names)} primeiros nomes e {len(last_names)} sobrenomes")

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

def generate_long_name(first_names, last_names):
    first_part = f"{random.choice(first_names)} {random.choice(first_names)}"
    last_part = " ".join(random.choice(last_names) for _ in range(random.randint(2, 3)))
    return f"{first_part} {last_part}"

def generate_name():
    r = random.random()
    if r < 0.5:
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    elif r < 0.8:
        return f"{random.choice(first_names)} {random.choice(first_names)} {random.choice(last_names)}"
    else:
        return generate_long_name(first_names, last_names)

# --- Contextos variados ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_contexts.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    contexts = json.load(f)

# --- Gerar exemplos ---
examples = []
NUM_EXAMPLES = 5000  # aumentar para 50k+

while len(examples) < NUM_EXAMPLES:
    name = generate_name()
    address = faker.address().replace("\n", ", ")
    cep = faker.postcode()

    # Aleatorizar maiúsculas/minúsculas e remover acentos
    if random.random() < 0.2:
        name = remove_accents(random_case(name))

    context = random.choice(contexts)
    text = context.format(name=name, address=address, cep=cep)

    entities = []
    # Nome
    start_name = text.index(name)
    end_name = start_name + len(name)
    entities.append((start_name, end_name, "PERSON"))
    
    # Endereço
    if "{address}" in context:
        start_addr = text.index(address)
        end_addr = start_addr + len(address)
        entities.append((start_addr, end_addr, "ADDRESS"))
    
    # CEP
    if "{cep}" in context:
        start_cep = text.index(cep)
        end_cep = start_cep + len(cep)
        entities.append((start_cep, end_cep, "CEP"))

    examples.append((text, {"entities": entities}))

# --- Salvar dataset ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_training.json"
DATA_PATH.parent.mkdir(exist_ok=True)
with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(examples, f, ensure_ascii=False, indent=2)

print(f"{len(examples)} exemplos anotados gerados e salvos em {DATA_PATH}")
