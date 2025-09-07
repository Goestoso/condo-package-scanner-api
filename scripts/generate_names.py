import json
import random
import unicodedata
from pathlib import Path

# --- Listas de nomes ---

first_names = [
    "Ruan", "Maria", "João", "Ana", "Lucas", "Beatriz", "Carlos", "Fernanda",
    "Maurício", "Gabriel", "Juliana", "Paulo", "Renata", "Eduardo", "Carla",
    "Thiago", "Larissa", "André", "Patrícia", "Rafael", "Camila", "Felipe", 
    "Aline", "Vitor", "Bruna", "Daniel", "Simone", "Rodrigo", "Juliana", 
    "Marcos", "Carolina", "Mateus", "Bianca", "Gustavo", "Letícia", "Igor", "Natália"
]

middle_names = [
    "Rodrigues", "Oliveira", "da", "de", "dos", "do", "Lima", "Souza", "Almeida",
    "Pereira", "Silva", "Santos", "Costa", "Cardoso", "Ferreira", "Barbosa", 
    "Machado", "Medeiros", "Cavalcanti", "Gonçalves", "Nunes", "Teixeira", "Marques"
]

last_names = [
    "Silva", "Souza", "Lima", "Oliveira", "Pereira", "Costa", "Almeida", "Dias",
    "Ribeiro", "Martins", "Ferreira", "Gomes", "Carvalho", "Barbosa", "Mendes",
    "Moura", "Siqueira", "Nascimento", "Assis", "Moreira", "Rocha", "Pinto"
]

# --- Contextos variados (50+) ---

contexts = [
    "{} mora em São Gonçalo",
    "Entregar pacote para {}",
    "Nome do destinatário: {}",
    "Residência de {}: Rua das Flores",
    "O pacote é para {}",
    "Cliente {} comprou um item",
    "Destinatário: {}",
    "Enviar encomenda para {}",
    "Endereço de {}",
    "Pedido para {}",
    "Recebedor: {}",
    "Informações do cliente: {}",
    "Volume enviado a {}",
    "Pacote destinado a {}",
    "Nome no DANFE: {}",
    "Entrega registrada para {}",
    "Pedido confirmado por {}",
    "Assinatura de {}",
    "Contato principal: {}",
    "Morador: {}",
    "Residência: {}",
    "CPF/Cliente: {}",
    "Endereço de entrega: {}",
    "Pessoa responsável: {}",
    "Atenção para {}",
    "Entrega expressa para {}",
    "Destinatário final: {}",
    "Destinatário: {}",
    "Remetente: {}",
    "Nota fiscal do cliente {}",
    "Item enviado a {}",
    "Comprovante de entrega: {}",
    "Confirmar entrega para {}",
    "Registro de encomenda: {}",
    "Remessa: {}",
    "Recebido por {}",
    "Confirmação do destinatário {}",
    "Volume 1: {}",
    "Nome no pacote: {}",
    "Cliente: {}",
    "Produto destinado a {}",
    "Etiqueta de envio: {}",
    "Transporte para {}",
    "Destinatário correto: {}",
    "Entrega agendada para {}",
    "Confirmação de pedido: {}",
    "Entrega realizada para {}",
    "Pacote recebido por {}",
    "Nota de envio: {}",
    "Documento de entrega: {}",
    "Cliente final: {}",
    "Recebimento de {}",
    "Envio concluído para {}",
    "{} mora na Rua das Flores, nº 123",
    "Entregar pacote para {} no Condomínio Azul, apto 202",
    "Destinatário: {}",
    "Residência de {}: Bairro dos Girassóis, 45",
    "O pacote é para {} na Rua das Acácias",
    "Cliente {} comprou um item",
    "Enviar para {} - Rua das Orquídeas, 34, Bloco B",
    "Nome do destinatário: {}",
    "A encomenda deve ser entregue a {} na Rua do Sol, 50",
    "Endereço do destinatário {}: Avenida Brasil, 200",
    "{} - Rua da Paz, apartamento 12",
    "Pacote destinado a {}",
    "Entregar na casa de {} - Etrada Primavera, 77",
    "Destinatário do pedido: {}",
    "Residência: {} - Rua Vitória, 123",
    "Envio para {} - Rua das Magnólias, 88, apto 3A",
    "Cliente {} recebeu o pedido",
    "Para {} na Rua dos Cravos, 101",
    "Pacote a ser entregue a {} - Rodovia Estrela, 210",
    "{} - Condomínio Jardim das Flores, apto 101",
    "Rua das Palmeiras, nº 45, {}",
    "{} - Rua das Orquídeas, Bloco C, apto 305",
    "Entrega: {} - Parque das Acácias, 99",
    "Destinatário {} - Praça da Alegria, 123",
    "Cliente: {} - Pq do Horizonte, 500",
    "Rua Vitória, nº 88, {}",
    "{} - Bairro Hortênsias, apto 202",
    "Pacote para {} - Praça do Sol, Bloco A, apto 101",
    "Residência {} - Estrada das Flores, 78",
    "Entregar encomenda a {} - Parque dos Cravos, apto 12",
    "{} recebeu a encomenda - Rua Primavera, 101",
    "Destinatário final: {}",
    "{} - Rua dos Lírios, 55",
    "Endereço para entrega: {} - Rua da Paz, 200",
    "Cliente {} - Rua das Magnólias, 67, apto 3B",
    "{} - Av das Acácias, apto 45",
    "Entrega em mãos: {}",
    "Destinatário principal: {} - Rodovia do Horizonte, 89",
    "{} - Rua das Palmeiras, apto 202",
    "Pacote destinado a {} - Rua do Sol, nº 210",
    "{} - Rua das Hortênsias, Bloco B",
    "Residência de {} - Rua da Alegria, 100",
    "Cliente {} - Rua dos Girassóis, apto 3C",
    "Entrega urgente para {}",
    "{} - Rua das Flores, Bloco A, apto 101",
    "Destinatário do pedido: {} - Rua do Sol, 55",
    "Pacote a ser entregue a {} - Rua da Paz, nº 77",
    "Av Primavera, nº 12, {}",
    "Enviar para {} - Av. Vitória, apto 202",
    "{} - Rua das Magnólias, apto 3A",
    "Entrega para {} - Rua dos Lírios, nº 88",
    "Destinatário: {} - Rua das Hortênsias, apto 101",
    "{} - Av das Palmeiras, Bloco C, apto 305"
]

# --- Funções auxiliares ---
def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def random_case(text):
    r = random.random()
    if r < 0.33:
        return text.lower()
    elif r < 0.66:
        return text.upper()
    else:
        return text.title()

def random_abbreviation(name):
    parts = name.split()
    if len(parts) == 3 and random.random() < 0.3:
        return f"{parts[0]} {parts[1][0]}. {parts[2]}"
    return name

# --- Gerar exemplos ---
examples = []
NUM_EXAMPLES = 10000

while len(examples) < NUM_EXAMPLES:
    first = random.choice(first_names)
    middle = random.choice(middle_names)
    last = random.choice(last_names)
    name = f"{first} {middle} {last}"

    # Variações
    name_var = random_case(name)
    if random.random() < 0.2:
        name_var = remove_accents(name_var)
    name_var = random_abbreviation(name_var)

    # Escolher contexto ou nome isolado
    if random.random() < 0.2:
        text = name_var  # nome isolado
    else:
        context = random.choice(contexts)
        text = context.format(name_var)

    # Introduzir ruído aleatório (números, caracteres)
    if random.random() < 0.1:
        text += f" {random.randint(1000,9999)}"
    if random.random() < 0.05:
        text += " ###"

    # Garantir índice correto
    start = text.index(name_var)
    end = start + len(name_var)
    examples.append((text, {"entities": [(start, end, "PERSON")]}))

# --- Salvar dataset ---
DATA_PATH = Path(__file__).parent.parent / "data" / "names_training.json"
DATA_PATH.parent.mkdir(exist_ok=True)
with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(examples, f, ensure_ascii=False, indent=2)

print(f"{len(examples)} exemplos anotados gerados e salvos em {DATA_PATH}")