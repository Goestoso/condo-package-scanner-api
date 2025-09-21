import spacy
from spacy.training import Example
from spacy.tokens import DocBin
from spacy.util import minibatch, compounding
from pathlib import Path
import random

# --- Caminhos ---
DATA_DIR = Path(__file__).parent.parent / "data"
TRAIN_EX = DATA_DIR / "street_training.spacy"  # dataset curto focado em STREET
MODEL_DIR = Path(__file__).parent.parent / "models" / "address_ner_old_3" / "model-last"
OUTPUT_DIR = Path(__file__).parent.parent / "models" / "address_ner"

# --- Config ---
MAX_EPOCHS = 2
DROP_OUT = 0.2
BATCH_SIZE = 16
USE_GPU = True

# --- Configurar GPU ---
if USE_GPU and spacy.prefer_gpu():
    spacy.require_gpu()
    print("GPU ativada")
else:
    print("Usando CPU")

# --- Carregar modelo existente ---
nlp = spacy.load(MODEL_DIR)
optimizer = nlp.resume_training()

# --- Funções para carregar exemplos ---
def load_examples(spacy_file, nlp_model):
    doc_bin = DocBin().from_disk(spacy_file)
    examples = []
    for ref_doc in doc_bin.get_docs(nlp_model.vocab):
        pred_doc = nlp_model(ref_doc.text)
        examples.append(Example(pred_doc, ref_doc))
    return examples

# --- Carregar dados ---
train_examples = load_examples(TRAIN_EX, nlp)

# --- Fine-tuning incremental ---
for epoch in range(1, MAX_EPOCHS + 1):
    random.shuffle(train_examples)
    losses = {}
    example_count = 0
    print(f"\nEpoch {epoch}/{MAX_EPOCHS}")
    
    batch_sizes = compounding(4.0, BATCH_SIZE, 1.001)
    for batch in minibatch(train_examples, size=batch_sizes):
        nlp.update(batch, drop=DROP_OUT, losses=losses)
        example_count += len(batch)

    print(f"Exemplos processados: {example_count}, Loss NER: {losses.get('ner',0):.2f}")

# --- Salvar modelo atualizado ---
OUTPUT_DIR.mkdir(exist_ok=True)
nlp.to_disk(OUTPUT_DIR / "model-last")
print(f"\n✔ Modelo STREET fine-tuned salvo em {OUTPUT_DIR / 'model-last'}")
