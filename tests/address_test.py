import spacy
from pathlib import Path

# --- Caminho do modelo existente ---
MODEL_PATH = Path(__file__).parent.parent / "models" / "address_ner" / "model-last"

nlp = spacy.load(MODEL_PATH)

# --- Teste rápido ---
test_texts = [
    "1035 Séne Emissão 2023 Rua Jonas Fonseca 250 Condominio marrom apartamento 404 São Gonçalo RJ Ruan Rodrigues Silva Bairro Colubande ESSE UMA Encontre mais próxima Hub ENETENTE Rua Ébano 111 Térreo RJ",
    "Moldes Vestido Pet Nessas presa Destinatário Mauro Rua dos Pregos 476 Condominio Black Apartamento 12 SP Remetente ueitom vitor lua Tiradentes casa Campos MG",
    "1000 INI Destinatário João Dias Rua Jonas Fonseca 250 Condomínio azul apartamento 112  São Gonçalo Remotento SIGEP WEB Ambiente Homologação",
    "DIADII TER 2025 8398 datguei Sávio Pereira Castro Entergo Avenida Brigadeiro Luis Antônio 1272 Bela  Cidade destin Complemento Auto pecas Reino have accos partamento Referencia frente Pepe próximo Igreja Universal",
    "Growth SUPPLEMENTS Contrato SPE Recebedor Assinatura DESTINATÁRIO PEDRO HENRIQUE PARIZOTI MEYER RUA IARA 476 PARQUE DOS CAMARGOS 06436 160 BARUERI Remetente GROWTH SUPPLEMENTS PRODUTOS ALIMENTÍCIOS LTDA AVENIDA WILSON LEMOS 2850 SANTA LUZIA 88200 958 TIJUCAS",
    "Destinario Ana Moraes Endereco ANA Casa VILA MARIA HELENA CARAPICUIBA  Caixa 001 001 DELIVERY TRANSPORTES LTDA 999226 CAR Norma",
    "Flex Set 2322000 CARAPICUIBA CARAPICUÍBA Endereço Rua Ana Complemento Bairro Vila Maria Heler Destinatario Jonas Moraes PRINTER"
]


print("\nTeste rápido de reconhecimento de endereços:")
for text in test_texts:
    doc = nlp(text)
    print(f"TEXTO OCR:\n{text}\n")
    print("Entidades detectadas:")
    for ent in doc.ents:
        print(f"  {ent.text} → {ent.label_}")
