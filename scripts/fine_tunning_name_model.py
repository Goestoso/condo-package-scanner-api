import json
import random
import spacy
from spacy.tokens import DocBin
from pathlib import Path

# --- Carregar contextos de erro ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_errors.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    contexts = json.load(f)

# --- Dados de exemplo ---
first_names = ["Maria", "João", "Carlos", "Ana", "Lucas", "Fernanda", "Sávio", "Afonso", "Charles", "Douglas", "Ludmila", "Marta", "Agnes",
                     "Ronaldo", "Alex", "Paula", "Eliana", "Elaine", "Viviane", "Carmen", "Jéssica"]
last_names = ["Silva", "Souza", "Costa", "Oliveira", "Gomes", "Pereira", "Castilho",
                    "Guimarães","Maia","Tavares", "Carneiro", "Meira", "Maciel", "Torres"]
streets = ["Rua das Flores", "Avenida Brasil", "Rua 7 de Setembro", "Travessa do Sol"]
cities = ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba"]

NUM_EXAMPLES = 200  # pequeno dataset focado

def generate_name():
    r = random.random()
    if r < 0.15:
        # Apenas primeiro nome
        return random.choice(first_names)
    elif r < 0.25:
        # Apenas sobrenome
        return random.choice(last_names)
    elif r < 0.55:
        # Nome + sobrenome
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    elif r < 0.85:
        # Dois nomes + sobrenome
        return f"{random.choice(first_names)} {random.choice(first_names)} {random.choice(last_names)}"
    else:
        # Nome longo: 2-3 nomes + 1-2 sobrenomes + sufixo opcional
        first_part = " ".join(random.choice(first_names) for _ in range(random.randint(2,3)))
        last_part = " ".join(random.choice(last_names) for _ in range(random.randint(1,2)))
        suffix = random.choice(["", " Filho", " Neto", " Junior"])
        return f"{first_part} {last_part}{suffix}"


def generate_address():
    return random.choice(streets)

def generate_number():
    return str(random.randint(1, 9999))

def generate_city():
    return random.choice(cities)

examples = []
for _ in range(NUM_EXAMPLES):
    context = random.choice(contexts)
    name = generate_name()
    address = generate_address()
    city = generate_city()
    number = generate_number()
    states = ["SP", "RJ", "MG", "PR"]
    state = random.choice(states)

    text = context.format(name=name, address=address, city=city, number=number, state=state)
    
    start = text.find(name)
    end = start + len(name)
    examples.append((text, {"entities": [(start, end, "PERSON")]}))

# --- Split treino/dev 80/20 ---
random.shuffle(examples)
split = int(0.8 * len(examples))
train_examples = examples[:split]
dev_examples = examples[split:]

# --- Salvar em spaCy ---
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

def to_spacy(examples, path):
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
    doc_bin.to_disk(path)
    
with open(DATA_DIR / "fine_tuning_train.json", "w", encoding="utf-8") as f:
    json.dump(train_examples, f, ensure_ascii=False, indent=2)
with open(DATA_DIR / "fine_tuning_dev.json", "w", encoding="utf-8") as f:
    json.dump(dev_examples, f, ensure_ascii=False, indent=2)

to_spacy(train_examples, DATA_DIR / "fine_tuning_train.spacy")
to_spacy(dev_examples, DATA_DIR / "fine_tuning_dev.spacy")

print("✅ Fine-tuning dataset gerado!")
