import spacy
from pathlib import Path

# --- Caminho do modelo existente ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "name_ner" / "model-last"

nlp = spacy.load(MODEL_PATH)

# --- Teste rápido ---
test_texts = [
    "Cliente João Pedro Pereira Silva comprou um item",
    "Entregar pacote para Ruan Silva Ribeiro",
    "Maria Costa Dias recebeu o pedido",
    "rua Rosa Vermelha, 315, Osasco, São Paulo João Dias Araújo Filho Remessa 12345",
    "Fagner Ruiz",
    "1035 Séne Emissão 2023 Rua Jonas Fonseca 250 Condominio marrom apt 404 São Gonçalo RJ Ruan Rodrigues Silva Bairro Colubande ESSE UMA Encontre mais próxima Hub ENETENTE Rua Ébano 111 Térreo RJ",
    "Moldes Vestido Pet Nessas presa Destinatário Mauro Rua dos Pregos 476 Condomíno Black Apt 12 SP Remetente ueitom vitor lua Tiradentes casa Campos MG",
    "1000 INI Destinatário João Dias Rua Jonas Fonseca 250 Condomínio azul apartamento 112  São Gonçalo Remotento SIGEP WEB Ambiente Homologação"
]

print("\nTeste rápido de reconhecimento de nomes:")
for text in test_texts:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    print(f"Texto: '{text}' -> Nomes detectados: {names}")