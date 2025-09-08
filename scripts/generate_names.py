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
    first_part = " ".join(random.choice(first_names) for _ in range(random.randint(2, 3)))
    last_part = " ".join(random.choice(last_names) for _ in range(random.randint(2, 3)))
    return f"{first_part} {last_part}"

def generate_name():
    r = random.random()
    if r < 0.2:
        return random.choice(first_names)
    elif r < 0.6:
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    elif r < 0.9:
        return f"{random.choice(first_names)} {random.choice(first_names)} {random.choice(last_names)}"
    else:
        return generate_long_name(first_names, last_names)

# --- Carregar contextos ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_contexts.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    contexts = json.load(f)

# --- Gerar exemplos ---
examples = []
NUM_EXAMPLES = 10000

while len(examples) < NUM_EXAMPLES:
    name = generate_name()
    address = faker.address().replace("\n", ", ")
    cep = faker.postcode()
    
    context = random.choice(contexts)
    text = context.format(name=name, address=address, cep=cep)

    # Inserir ruído aleatório após a criação do texto
    if random.random() < 0.1:
        text += f" {random.randint(1000, 9999)}"

    # Aleatorizar maiúsculas/minúsculas ou remover acentos **sem quebrar offsets**
    final_text = text
    if random.random() < 0.2:
        # aplicar transformações no texto inteiro para manter offsets
        final_text = remove_accents(final_text)
        # ou random_case(final_text) se quiser variar capitalização
    
    # Calcular offset de forma robusta
    start_name = final_text.find(name)
    if start_name != -1:
        end_name = start_name + len(name)
        entities = [(start_name, end_name, "PERSON")]
    else:
        entities = []

    examples.append((final_text, {"entities": entities}))

# --- Salvar dataset ---
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "names_training.json"
OUTPUT_PATH.parent.mkdir(exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(examples, f, ensure_ascii=False, indent=2)

print(f"{len(examples)} exemplos anotados gerados e salvos em {OUTPUT_PATH}")
