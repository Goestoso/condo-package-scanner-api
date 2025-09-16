import spacy
from spacy.training import Example
from spacy.scorer import Scorer
from spacy.tokens import DocBin
from spacy.util import minibatch
from pathlib import Path
import random

# --- Caminhos ---
DATA_DIR = Path(__file__).parent.parent / "data"
TRAIN_EX = DATA_DIR / "names_training.spacy"   # converti para .spacy
DEV_EX = DATA_DIR / "names_dev.spacy"
MODEL_DIR = Path(__file__).parent.parent / "models" / "name_ner_old" / "model-last"
OUTPUT_DIR = Path(__file__).parent.parent / "models" / "name_ner"

# --- Config ---
MAX_EPOCHS = 5
DROP_OUT = 0.2
BATCH_SIZE = 16
USE_GPU = True

# --- Configurar GPU antes de carregar modelo ---
if USE_GPU and spacy.prefer_gpu():
    spacy.require_gpu()
    print("GPU ativada")
else:
    print("Usando CPU")

nlp = spacy.load(MODEL_DIR)
optimizer = nlp.resume_training()

# --- Função para carregar exemplos de treino ---
def load_train_examples(spacy_file, nlp_model):
    doc_bin = DocBin().from_disk(spacy_file)
    examples = [Example(doc, doc) for doc in doc_bin.get_docs(nlp_model.vocab)]
    return examples

# --- Função para criar exemplos do dev set corretamente ---
def load_dev_examples(spacy_file, nlp_model):
    doc_bin = DocBin().from_disk(spacy_file)
    examples = []
    for ref_doc in doc_bin.get_docs(nlp_model.vocab):
        pred_doc = nlp_model(ref_doc.text)  # gerar predição
        example = Example(pred_doc, ref_doc)
        examples.append(example)
    return examples

train_examples = load_train_examples(TRAIN_EX, nlp)
dev_examples = load_dev_examples(DEV_EX, nlp)

# --- Treino incremental ---
for epoch in range(1, MAX_EPOCHS + 1):
    random.shuffle(train_examples)
    losses = {}
    example_count = 0

    print(f"\nEpoch {epoch}/{MAX_EPOCHS}")
    print(f"{'E #':<5} {'LOSS':<10} {'N':<6} {'ENTS_F':<7} {'ENTS_P':<7} {'ENTS_R':<7} {'F1_SCORE':<7}")

    for batch in minibatch(train_examples, size=BATCH_SIZE):
        nlp.update(batch, drop=DROP_OUT, losses=losses)
        example_count += len(batch)

    # Avaliação completa no dev set
    scorer = Scorer()
    scores = scorer.score(dev_examples)
    f1_score = scores["ents_f"]

    print(f"{example_count:<5} {losses.get('ner',0):<10.2f} {len(train_examples):<6} "
          f"{scores['ents_f']*100:<7.2f} {scores['ents_p']*100:<7.2f} "
          f"{scores['ents_r']*100:<7.2f} {f1_score*100:<7.2f}")

# --- Salvar modelo atualizado ---
OUTPUT_DIR.mkdir(exist_ok=True)
nlp.to_disk(OUTPUT_DIR / "model-last")
print(f"\n✔ Modelo atualizado salvo em {OUTPUT_DIR / 'model-last'}")
