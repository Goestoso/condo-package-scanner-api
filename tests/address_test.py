import spacy
from pathlib import Path

# --- Caminho do modelo existente ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "address_ner" / "model-last"

nlp = spacy.load(MODEL_PATH)

# --- Teste rápido ---
test_texts = [
    "1035 Séne Emissão 2023 Rua Jonas Fonseca 250 Condominio marrom apt 404 São Gonçalo RJ Ruan Rodrigues Silva Bairro Colubande ESSE UMA Encontre mais próxima Hub ENETENTE Rua Ébano 111 Térreo RJ",
    "Moldes Vestido Pet Nessas presa Destinatário Mauro Rua dos Pregos 476 Condomíno Black Apt 12 SP Remetente ueitom vitor lua Tiradentes casa Campos MG",
    "1000 INI Destinatário João Dias Rua Jonas Fonseca 250 Condomínio azul apartamento 112  São Gonçalo Remotento SIGEP WEB Ambiente Homologação"
]


print("\nTeste rápido de reconhecimento de endereços:")
for text in test_texts:
    doc = nlp(text)
    print(f"TEXTO OCR:\n{text}\n")
    print("Entidades detectadas:")
    for ent in doc.ents:
        print(f"  {ent.text} → {ent.label_}")
