from faker import Faker
import random

faker = Faker("pt_BR")

# Extrair base de nomes e sobrenomes
first_names = set()
last_names = set()

for _ in range(5000):
    name = faker.name().split()
    if len(name) >= 2:
        first_names.add(name[0])
        last_names.add(name[-1])

first_names = list(first_names)
last_names = list(last_names)

print(f"Coletados {len(first_names)} primeiros nomes e {len(last_names)} sobrenomes")

# Função para criar nomes compostos
def generate_name():
    # 50% chance de nome simples
    if random.random() < 0.5:
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    # 40% chance de nome composto
    elif random.random() < 0.6:
        return f"{random.choice(first_names)} {random.choice(first_names)} {random.choice(last_names)}"

    # 20% chance de nome longo
    elif random.random() < 0.8:
        return f"{random.choice(first_names)} {random.choice(first_names)} {random.choice(last_names)} {random.choice(last_names)}"
    else:
        return generate_long_name(first_names, last_names)  # longo/gigante
    

def generate_long_name(first_names, last_names):
    # dois primeiros nomes
    first_part = f"{random.choice(first_names)} {random.choice(first_names)}"
    
    # dois ou três sobrenomes
    last_part = " ".join(random.choice(last_names) for _ in range(random.randint(2, 3)))
    
    return f"{first_part} {last_part}"

# Teste
for _ in range(10):
    print(generate_name())


