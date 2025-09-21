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
    "Spe Destinatario Pedro Henrique Parizoti Meyer Rua Iara 476 Parque Dos Camargos Barueri Remetente Produtos Alimenticios Ltda Avenida Wilson Lemos 2850 Santa Luzia Tijucas",
    "Destinario Ana Moraes Endereco ANA Casa VILA MARIA HELENA CARAPICUIBA  Caixa 001 001 DELIVERY TRANSPORTES LTDA 999226 CAR Norma",
    "Flex Set 2322000 CARAPICUIBA CARAPICUÍBA Endereço Rua Ana Complemento Bairro Vila Maria Heler Destinatario Jonas Moraes PRINTER",
    "Uso Protocolo Simplific Rodovia PR Animais MG Ado PI 395 SE 9 Emissao Destinatario SP Cliente Sarah Olive Rua Xv Novembro 500 Bloco 2 Apartamento 12 Jardim Gabr Jandira SP Condominio Tel Mega Rota PB Mm Nto Sar SP Not"
]


print("\nTeste rápido de reconhecimento de endereços:")
for text in test_texts:
    doc = nlp(text)
    print(f"TEXTO OCR:\n{text}\n")
    print("Entidades detectadas:")
    for ent in doc.ents:
        print(f"  {ent.text} → {ent.label_}")
