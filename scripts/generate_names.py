import json
import random
import unicodedata
from pathlib import Path
from faker import Faker
import spacy
from spacy.tokens import DocBin

faker = Faker("pt_BR")

# --- Base de nomes e sobrenomes ---
first_names = set()
last_names = set()
for _ in range(5000):
    name = faker.name().split()
    if len(name) >= 2:
        first_names.add(name[0])
        last_names.add(name[-1])

# Extras específicos
extra_first_names = ["Mauro","Anderson","Fabiana","Félix","Sérgio","Aline","Cláudio","Cléber",
                     "Fábio","Verônica","Osvaldo","Meire","Neusa","Fagner","Ruan","Roberto",
                     "Sávio", "Afonso", "Charles", "Douglas", "Ludmila", "Marta", "Agnes",
                     "Ronaldo", "Alex", "Paula", "Eliana", "Elaine", "Viviane", "Carmen"]
extra_last_names = ["Góes","Aguiar","Magalhães","Coelho","Ruiz","Diniz","Xavier","Castilho",
                    "Guimarães","Maia","Tavares", "Carneiro", "Meira", "Maciel", "Torres"]

# Lista de estados e siglas do Brasil
states = [
    ("Acre", "AC"), ("Alagoas", "AL"), ("Amapá", "AP"), ("Amazonas", "AM"),
    ("Bahia", "BA"), ("Ceará", "CE"), ("Distrito Federal", "DF"), ("Espírito Santo", "ES"),
    ("Goiás", "GO"), ("Maranhão", "MA"), ("Mato Grosso", "MT"), ("Mato Grosso do Sul", "MS"),
    ("Minas Gerais", "MG"), ("Pará", "PA"), ("Paraíba", "PB"), ("Paraná", "PR"),
    ("Pernambuco", "PE"), ("Piauí", "PI"), ("Rio de Janeiro", "RJ"), ("Rio Grande do Norte", "RN"),
    ("Rio Grande do Sul", "RS"), ("Rondônia", "RO"), ("Roraima", "RR"), ("Santa Catarina", "SC"),
    ("São Paulo", "SP"), ("Sergipe", "SE"), ("Tocantins", "TO")
]

# Escolher aleatoriamente um estado
state_full, state_abbr = random.choice(states)

first_names.update(extra_first_names)
last_names.update(extra_last_names)
first_names = sorted(first_names)
last_names = sorted(last_names)

# --- Funções auxiliares ---
def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def random_case(text):
    r = random.random()
    if r < 0.33: return text.lower()
    elif r < 0.66: return text.upper()
    else: return text.title()

def generate_long_name():
    first_part = " ".join(random.choice(first_names) for _ in range(random.randint(2,3)))
    last_part = " ".join(random.choice(last_names) for _ in range(random.randint(2,3)))
    # Adiciona opcionalmente sufixo
    suffix = random.choice(["", " Filho", " Neto", " Junior"])
    return f"{first_part} {last_part}{suffix}"

def generate_name():
    r = random.random()
    if r < 0.15:
        # Apenas primeiro nome
        return random.choice(first_names)
    elif r < 0.25:
        # Apenas sobrenome
        return random.choice(last_names)
    elif r < 0.55:
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    elif r < 0.85:
        return f"{random.choice(first_names)} {random.choice(first_names)} {random.choice(last_names)}"
    else:
        return generate_long_name()

# --- Carregar contextos ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_contexts.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    contexts = json.load(f)

# --- Gerar exemplos ---
examples = []
NUM_EXAMPLES = 10000
NEGATIVE_RATIO = 0.15  # 15% sem nomes

while len(examples) < NUM_EXAMPLES:
    if random.random() < NEGATIVE_RATIO:
        # Exemplo negativo: apenas endereço/CEP, sem nome
        text = f"{faker.street_name()}, {random.randint(1,999)} - {faker.city()} - {faker.postcode()}"
        examples.append((text, {"entities": []}))
        continue

    name = generate_name()
    address = faker.street_name()
    number = str(random.randint(1, 9999))
    city = faker.city()
    state = random.choice([state_full, state_abbr])
    cep = faker.postcode()
    context = random.choice(contexts)

    # Usar marcador para offsets seguros
    marker = "<<NAME>>"
    text = context.format(name=marker, address=address, number=number, city=city, state=state, cep=cep)

    # Substituir marcador pelo nome final
    start = text.find(marker)
    final_text = text.replace(marker, name, 1)
    end = start + len(name)

    # Aleatorizar maiúsculas/minúsculas ou remover acentos
    if random.random() < 0.2:
        final_text = remove_accents(final_text)
    elif random.random() < 0.2:
        final_text = random_case(final_text)

    entities = [(start, end, "PERSON")]
    examples.append((final_text, {"entities": entities}))

print(f"{len(examples)} exemplos gerados")

# --- Split treino/dev (80/20) ---
random.shuffle(examples)
split = int(len(examples) * 0.8)
train_examples = examples[:split]
dev_examples = examples[split:]

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- Salvar JSON ---
with open(DATA_DIR / "names_training.json", "w", encoding="utf-8") as f:
    json.dump(train_examples, f, ensure_ascii=False, indent=2)
with open(DATA_DIR / "names_dev.json", "w", encoding="utf-8") as f:
    json.dump(dev_examples, f, ensure_ascii=False, indent=2)

# --- Salvar em spaCy ---
def to_spacy(examples, output_path):
    nlp = spacy.blank("pt")
    doc_bin = DocBin()
    for text, annot in examples:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annot.get("entities", []):
            span = doc.char_span(start, end, label=label)
            if span:
                ents.append(span)
        doc.ents = ents
        doc_bin.add(doc)
    doc_bin.to_disk(output_path)

to_spacy(train_examples, DATA_DIR / "names_training.spacy")
to_spacy(dev_examples, DATA_DIR / "names_dev.spacy")

print(f"Treino salvo em {DATA_DIR/'names_training.spacy'}")
print(f"Dev salvo em {DATA_DIR/'names_dev.spacy'}")
