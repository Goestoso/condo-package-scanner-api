import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
from pathlib import Path
import json
import random
from faker import Faker

faker = Faker("pt_BR")

# --- Caminhos ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "name_ner"  # modelo existente
DATA_CONTEXTS_PATH = Path(__file__).parent.parent / "data" / "names_contexts.json"

# --- Nomes novos que queremos adicionar ---
novos_first_names = ["Mauro", "Leandro", "Fabiana", "Marcio", "Roberto", "Cristina"]
novos_last_names = ["Guimarães", "Alcântara", "Coelho"]

# --- Carregar contextos ---
with open(DATA_CONTEXTS_PATH, "r", encoding="utf-8") as f:
    contexts = json.load(f)

# --- Funções de geração de nomes ---
def generate_long_name(first_names, last_names):
    first_part = " ".join(random.choice(first_names) for _ in range(random.randint(2, 3)))
    last_part = " ".join(random.choice(last_names) for _ in range(random.randint(2, 3)))
    return f"{first_part} {last_part}"

def generate_name():
    r = random.random()
    if r < 0.2:
        return random.choice(novos_first_names)
    elif r < 0.6:
        return f"{random.choice(novos_first_names)} {random.choice(novos_last_names)}"
    elif r < 0.9:
        return f"{random.choice(novos_first_names)} {random.choice(novos_last_names)} {random.choice(novos_last_names)}"
    else:
        return generate_long_name(novos_first_names, novos_last_names)

# --- Gerar exemplos para treinamento incremental ---
examples = []
NUM_EXAMPLES = 200  # ajustar conforme necessário
for _ in range(NUM_EXAMPLES):
    name = generate_name()
    address = faker.address().replace("\n", ", ")
    cep = faker.postcode()
    context = random.choice(contexts)
    text = context.format(name=name, address=address, cep=cep)

    try:
        start_name = text.index(name)
        end_name = start_name + len(name)
        entities = [(start_name, end_name, "PERSON")]
        examples.append((text, {"entities": entities}))
    except ValueError:
        pass  # fallback se nome não estiver no texto

print(f"{len(examples)} exemplos gerados para novos nomes.")

# --- Carregar modelo existente ---
nlp = spacy.load(MODEL_PATH)
ner = nlp.get_pipe("ner")

# --- Treinamento incremental ---
optimizer = nlp.resume_training()
EPOCHS = 5
BATCH_SIZE = 16

for epoch in range(EPOCHS):
    random.shuffle(examples)
    losses = {}
    batches = minibatch(examples, size=BATCH_SIZE)
    for batch in batches:
        batch_examples = [Example.from_dict(nlp.make_doc(text), annots) for text, annots in batch]
        nlp.update(batch_examples, sgd=optimizer, losses=losses)
    print(f"Epoch {epoch + 1}/{EPOCHS} - Losses: {losses}")

# --- Salvar modelo atualizado ---
nlp.to_disk(MODEL_PATH)
print(f"Modelo atualizado salvo em: {MODEL_PATH}")
