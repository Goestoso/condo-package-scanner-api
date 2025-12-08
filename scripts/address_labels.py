import spacy
from spacy.tokens import DocBin
from spacy.training import Example
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
MODEL_DIR = Path(__file__).parent.parent / "models" / "address_ner_old_2" / "model-last"

nlp = spacy.load(MODEL_DIR)
ner = nlp.get_pipe("ner")
print("Labels atuais:", ner.labels)
