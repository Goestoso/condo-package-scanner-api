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
    "1000 INI Destinatário João Dias Rua Jonas Fonseca 250 Condomínio azul apartamento 112  São Gonçalo Remotento SIGEP WEB Ambiente Homologação",
    "DIADII TER 2025 8398 datguei Savio Pereira Castro Entergo Avenida Brigadeiro Luis Antonio 1272 Bela  Cidade destin Complemento Auto pecas Reino have accos partamento Referencia frente Pepe proximo Igreja Universal",
    "Growth SUPPLEMENTS Contrato SPE Recebedor Assinatura DESTINATÁRIO PEDRO HENRIQUE PARIZOTI MEYER RUA IARA 476 PARQUE DOS CAMARGOS 06436 160 BARUERI Remetente GROWTH SUPPLEMENTS PRODUTOS ALIMENTÍCIOS LTDA AVENIDA WILSON LEMOS 2850 SANTA LUZIA 88200 958 TIJUCAS",
    "Destinario Ana Moraes Endereco ANA Casa VILA MARIA HELENA CARAPICUIBA  Caixa 001 001 DELIVERY TRANSPORTES LTDA 999226 CAR Norma",
    "Flex Set 2322000 CARAPICUIBA CARAPICUÍBA Endereço Rua Ana Complemento Bairro Vila Maria Heler Destinatario Jonas Moraes PRINTER"
]

print("\nTeste rápido de reconhecimento de nomes:")
for text in test_texts:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    print(f"Texto: '{text}' -> Nomes detectados: {names}")