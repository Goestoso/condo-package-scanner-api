import spacy
from pathlib import Path

# --- Caminho do modelo existente ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "address_ner" / "model-last"

nlp = spacy.load(MODEL_PATH)

# --- Teste rápido ---
test_texts = [
    "1035 Séne Emissão 2023 Rua Jonas Fonseca 250 Condominio marrom apt 404 São Gonçalo Rio Janeiro Ruan Rodrigues Silva Bairro Colubande CEP 24451260 ESSE UMA Encontre mais próxima Hub ENETENTE Rua Ébano 111 Térreo Rio Janeiro CEP 20930060 RIL",
    "Moldes Vestido Pet Nessas presa Destinatário Mauro Rua dos Pregos 476 Condomíno Apt 701 13431112 São Paulo Remetente ueitom vitor lua Tiradentes casa Campos 37160000 Minas Garais",
    "1000 INI Destinatário João Dias Rua Jonas Fonseca 250 Condomínio azul apartamento 112 24451260 São Gonçalo Remotento SIGEP WEB Ambiente Homologação"
]


print("\nTeste rápido de reconhecimento de endereços:")
for text in test_texts:
    print(f"TEXTO OCR:\n{text}\n")
    doc = nlp(text)
    for ent in doc.ents:
        print("ENTIDADES:\n")
        print(ent.text, ent.label_)
