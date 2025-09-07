import spacy
from spacy.training import Example
import json
from pathlib import Path
import random
from spacy.util import minibatch

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
BATCH_SIZE = 8

for epoch in range(EPOCHS):
    random.shuffle(TRAIN_DATA)
    losses = {}
    
    # Treinamento por batches
    batches = minibatch(TRAIN_DATA, size=BATCH_SIZE)
    for batch in batches:
        examples = [Example.from_dict(nlp.make_doc(text), annots) for text, annots in batch]
        nlp.update(examples, sgd=optimizer, losses=losses)
    
    print(f"Epoch {epoch+1}/{EPOCHS} - Losses: {losses}")

# --- Salvar modelo treinado ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "name_ner"
MODEL_PATH.mkdir(parents=True, exist_ok=True)
nlp.to_disk(MODEL_PATH)
print(f"\nModelo treinado salvo em: {MODEL_PATH}")

# --- Teste rápido ---
print("\nTeste rápido de reconhecimento de nomes:")
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

for text in test_texts:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    print(f"Texto: '{text}' -> Nomes detectados: {names}")
