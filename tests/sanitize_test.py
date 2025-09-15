import sys
from pathlib import Path

# Adiciona a pasta src ao sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Agora dá para importar o módulo
from sticker import Sticker

text = "1035 Séne Emissão 2023 Rua Jonas Fonseca 250 Condominio marrom apt 404 São Gonçalo Rio Janeiro Ruan Rodrigues Silva Bairro Colubande  ESSE UMA Encontre mais próxima Hub ENETENTE Rua Ébano 111 Térreo Rio Janeiro  RIL"

x = Sticker("Ana.jpg")
print(f"OCR: {text}")
print(Sticker.sanitize(text=text,clear_cep=True))