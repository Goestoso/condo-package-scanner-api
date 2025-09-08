import spacy
from spacy.training import Example
from itertools import islice
from spacy.util import minibatch, compounding
from pathlib import Path
import json
import random

spacy.require_gpu()  # garante que o spaCy use a GPU

# --- Caminho do dataset ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_training.json"

# --- Criar pasta para checkpoints ---
CHECKPOINT_DIR = Path(__file__).parent.parent / "models" / "name_ner" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# --- Função para carregar dados em batches do disco ---
def load_data_in_batches(path, batch_size=5000):
    """Carrega os dados em pedaços (chunks) para não sobrecarregar memória."""
    with open(path, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    for i in range(0, len(all_data), batch_size):
        yield all_data[i:i + batch_size]

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

# --- Parâmetros de treino ---
EPOCHS = 5
INITIAL_BATCH = 256
MAX_BATCH = 512
iteration = 0

# --- Treinamento ---
for epoch in range(EPOCHS):
    losses = {}
    print(f"\n=== Epoch {epoch + 1}/{EPOCHS} ===")
    
    for batch_data in load_data_in_batches(DATA_PATH, batch_size=1000):
        random.shuffle(batch_data)
        # --- Gerar lista finita de batch_sizes ---
        # limite de 20 incrementos, por exemplo
        batch_sizes = list(islice(compounding(INITIAL_BATCH, MAX_BATCH, 1.5), 20))
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


# --- Salvar modelo final ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "name_ner"
MODEL_PATH.mkdir(parents=True, exist_ok=True)
nlp.to_disk(MODEL_PATH)
print(f"\nModelo final salvo em: {MODEL_PATH}")

# --- Teste rápido ---
test_texts = [
    "Cliente João Pedro Pereira Silva comprou um item",
    "Entregar pacote para Ruan Silva Ribeiro",
    "Maria Costa Dias recebeu o pedido",
    "rua Rosa Vermelha, 315, Osasco, São Paulo João Dias Araújo Filho Remessa 12345",
    "Destinatário: 23 Fagner Ruiz",
    "DANFE SIMPLIFICADO ETIQUETA A Saída NF 1035 Séne 1 Emissão 11 05 2023 105154 33230848 12441800013755001000001035 1928251620 Rua Jonas da Fonseca, 250, 1 Condominio marrom apt 404, São Gonçalo, Rio de Janeiro Ruan Rodrigues Da Silva Bairro Colubande CEP 24451 260 Pedido 230811BNH7M33K LEVAR ESSE PACOTE A UMA AGÊNCIA SHOPEE XPRESS. Encontre a agência mais próxima em wwshopeespress.com.br Soc Separação Shopee LM Hub XPRESS RIOO3 O BR2396162088837 O ENETENTE i ps e im Rua Ébano, 111, Térreo, Rio de Janeiro CEP 20930 060 SOC RIL",
    "Moldes De Vestido Pet Nessas presa Destinatário Mauro de uz Rua dos Pregos 476 Condomíno Ip Apt 701 13431 112 São Paulo Remetente ueitom vitor lua Tiradentes 86 casa Campos 37160 000 Minas Garais",
    "ou 1 CORREIOS ..m CORREIOS NF 112233 Pedido 0 Peso o 1000 II INI HI Nome Legível Documento Destinatário Volume 1 João Dias Rua Jonas da Fonseca, 250 Condomínio azul, apartamento 112 24451 260 São Gonçalo R J uu Remotento SIGEP WEB Ambiente de Homologação"
]

print("\nTeste rápido de reconhecimento de nomes:")
for text in test_texts:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    print(f"Texto: '{text}' -> Nomes detectados: {names}")
