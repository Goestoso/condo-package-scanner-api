import spacy
from spacy.training import Example
import json
from pathlib import Path
import random

# --- Caminho do dataset ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_training.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    TRAIN_DATA = json.load(f)

# --- Criar modelo vazio para português ---
nlp = spacy.blank("pt")

# --- Adicionar pipe NER ---
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

# --- Adicionar label 'PERSON' ---
ner.add_label("PERSON")

# --- Inicializar o modelo ---
optimizer = nlp.initialize()

# --- Treinamento ---
EPOCHS = 20
for epoch in range(EPOCHS):
    random.shuffle(TRAIN_DATA)
    losses = {}
    for text, annotations in TRAIN_DATA:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, annotations)
        nlp.update([example], sgd=optimizer, losses=losses)
    print(f"Epoch {epoch+1}/{EPOCHS} - Losses: {losses}")

# --- Salvar modelo treinado ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "name_ner"
MODEL_PATH.mkdir(parents=True, exist_ok=True)
nlp.to_disk(MODEL_PATH)
print(f"\nModelo treinado salvo em: {MODEL_PATH}")

# --- Teste rápido ---
print("\nTeste rápido de reconhecimento de nomes:")
test_texts = [
    "Cliente João Pereira Silva comprou um item",
    "Entregar pacote para Ruan Silva Ribeiro",
    "Maria Costa Dias recebeu o pedido",
    "João Dias",
    "[[]23 Fagner Ruiz"
]
for text in test_texts:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    print(f"Texto: '{text}' -> Nomes detectados: {names}")
