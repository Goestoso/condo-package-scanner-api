import spacy
from spacy.training import Example
from spacy.scorer import Scorer
from spacy.tokens import DocBin
from spacy.util import minibatch, compounding
from pathlib import Path
import random
import cupy  # Para checar GPU

# --- Caminhos ---
DATA_DIR = Path(__file__).parent.parent / "data"
TRAIN_EX = DATA_DIR / "address_training.spacy"
DEV_EX = DATA_DIR / "address_dev.spacy"
MODEL_DIR = Path(__file__).parent.parent / "models" / "address_ner_old_2" / "model-last"
OUTPUT_DIR = Path(__file__).parent.parent / "models" / "address_ner"

# --- Configurações ---
MAX_EPOCHS = 12
DROP_OUT = 0.5
BATCH_SIZE = 32
USE_GPU = True

# --- GPU ---
if USE_GPU and spacy.prefer_gpu():
    spacy.require_gpu()
    print("GPU ativada:", cupy.cuda.runtime.getDeviceCount(), "devices")
else:
    print("Usando CPU")

# --- Carregar modelo existente ---
nlp = spacy.load(MODEL_DIR)
optimizer = nlp.resume_training()

# --- Função de avaliação ---
def evaluate_model(nlp, dev_docs):
    """
    Avalia o modelo nlp no dev set dev_docs.
    dev_docs: lista de Docs de referência (original do DocBin)
    Retorna o dicionário de scores do Scorer.
    """
    examples = [Example(nlp(doc.text), doc) for doc in dev_docs]
    scorer = Scorer()
    return scorer.score(examples)  # <-- passar lista de Examples

# --- Carregar exemplos de treino ---
doc_bin_train = DocBin().from_disk(TRAIN_EX)
train_examples = [Example(doc, doc) for doc in doc_bin_train.get_docs(nlp.vocab)]

# --- Carregar dev_docs apenas uma vez ---
doc_bin_dev = DocBin().from_disk(DEV_EX)
dev_docs = list(doc_bin_dev.get_docs(nlp.vocab))

# --- Treino incremental ---
for epoch in range(1, MAX_EPOCHS + 1):
    random.shuffle(train_examples)
    losses = {}
    example_count = 0

    print(f"\nEpoch {epoch}/{MAX_EPOCHS}")
    print(f"{'E #':<5} {'LOSS':<10} {'N':<6} {'ENTS_F':<7} {'ENTS_P':<7} {'ENTS_R':<7} {'F1_SCORE':<7}")

    # Minibatches variáveis
    batch_sizes = compounding(4.0, BATCH_SIZE, 1.001)
    for batch in minibatch(train_examples, size=batch_sizes):
        nlp.update(batch, drop=DROP_OUT, losses=losses)
        example_count += len(batch)

    # Avaliação no dev set
    scores = evaluate_model(nlp, dev_docs)
    f1_score = scores["ents_f"]

    print(f"{example_count:<5} {losses.get('ner',0):<10.2f} {len(train_examples):<6} "
          f"{scores['ents_f']*100:<7.2f} {scores['ents_p']*100:<7.2f} "
          f"{scores['ents_r']*100:<7.2f} {f1_score*100:<7.2f}")

    print("\n--- Métricas por entidade ---")
    for label, metrics in scores.get("ents_per_type", {}).items():
        print(f"{label:<12} P: {metrics['p']*100:5.2f} | R: {metrics['r']*100:5.2f} | F1: {metrics['f']*100:5.2f}")

# --- Salvar modelo atualizado ---
OUTPUT_DIR.mkdir(exist_ok=True)
nlp.to_disk(OUTPUT_DIR / "model-last")
print(f"\n✔ Modelo atualizado salvo em {OUTPUT_DIR / 'model-last'}")
