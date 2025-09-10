import spacy
from spacy.training import Example
from itertools import islice
from spacy.util import minibatch, compounding
from pathlib import Path
import json
import random

spacy.require_gpu()

# --- Caminho do dataset ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_training.json"

# --- Caminho do modelo existente ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "name_ner"

# --- Criar pasta para checkpoints ---
CHECKPOINT_DIR = MODEL_PATH / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# --- Função para carregar dados em batches ---
def load_data_in_batches(path, batch_size=5000):
    with open(path, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    for i in range(0, len(all_data), batch_size):
        yield all_data[i:i + batch_size]

# --- Carregar modelo existente em vez de criar novo ---
print(f"Carregando modelo existente de: {MODEL_PATH}")
nlp = spacy.load(MODEL_PATH)

# --- Garantir que o NER esteja presente ---
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

# --- Adicionar label (não dá erro se já existir) ---
ner.add_label("PERSON")

# --- Inicializar otimizador no modo de continuação ---
optimizer = nlp.resume_training()

# --- Parâmetros de treino ---
EPOCHS = 5   # pode usar menos, já que é "refino"
INITIAL_BATCH = 256
MAX_BATCH = 512
iteration = 0

# --- Treinamento incremental ---
for epoch in range(EPOCHS):
    losses = {}
    print(f"\n=== Epoch {epoch + 1}/{EPOCHS} ===")
    
    for batch_data in load_data_in_batches(DATA_PATH, batch_size=1000):
        random.shuffle(batch_data)
        batch_sizes = list(islice(compounding(INITIAL_BATCH, MAX_BATCH, 1.3), 20))
        batch_sizes = [min(int(b), len(batch_data)) for b in batch_sizes if b <= len(batch_data)]
        
        for batch_size in batch_sizes:
            minibatches = minibatch(batch_data, size=batch_size)
            print(f"Gerando minibatches para batch_size={batch_size} com {len(batch_data)} exemplos")
            for mb in minibatches:
                iteration += 1
                examples = [Example.from_dict(nlp.make_doc(text), annots) for text, annots in mb]
                nlp.update(examples, sgd=optimizer, losses=losses)
                print(f"Epoch {epoch + 1}, Iteração {iteration}, Tamanho do batch: {len(mb)}, Losses: {losses}")

    print(f"Epoch {epoch + 1} - Losses: {losses}")
    
    # --- Salvar checkpoint a cada epoch ---
    checkpoint_path = CHECKPOINT_DIR / f"epoch_{epoch + 1}"
    nlp.to_disk(checkpoint_path)
    print(f"Checkpoint salvo em: {checkpoint_path}")

# --- Salvar modelo atualizado ---
nlp.to_disk(MODEL_PATH)
print(f"\nModelo atualizado salvo em: {MODEL_PATH}")

# --- Teste rápido ---
test_texts = [
    "Cliente João Pedro Pereira Silva comprou um item",
    "Entregar pacote para Ruan Silva Ribeiro",
    "Maria Costa Dias recebeu o pedido",
    "rua Rosa Vermelha, 315, Osasco, São Paulo João Dias Araújo Filho Remessa 12345",
    "Fagner Ruiz",
    "1035 Séne Emissão 2023 Rua Jonas Fonseca, 250, Condominio marrom apt 404, São Gonçalo, Rio Janeiro Ruan Rodrigues Silva Bairro Colubande CEP 24451 260 ESSE UMA Encontre mais próxima Hub ENETENTE Rua Ébano, 111, Térreo, Rio Janeiro CEP 20930 060 RIL",
    "Moldes De Vestido Pet Nessas presa Destinatário Mauro de uz Rua dos Pregos 476 Condomíno Ip Apt 701 13431 112 São Paulo Remetente ueitom vitor lua Tiradentes 86 casa Campos 37160 000 Minas Garais",
    "..m 1000 INI Destinatário João Dias Rua Jonas Fonseca, 250 Condomínio azul, apartamento 112 24451 260 São Gonçalo Remotento SIGEP WEB Ambiente Homologação"
]

print("\nTeste rápido de reconhecimento de nomes:")
for text in test_texts:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    print(f"Texto: '{text}' -> Nomes detectados: {names}")

