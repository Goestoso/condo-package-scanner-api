import sys
from pathlib import Path

# Adiciona a pasta src ao sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Agora dá para importar o módulo
from sticker import Sticker

text = "1035 Séne Emissão 2023 Rua Jonas Fonseca 250 Condominio marrom apt 404 São Gonçalo Rio Janeiro Ruan Rodrigues Silva Bairro Colubande CEP 24451 260 ESSE UMA Encontre mais próxima Hub ENETENTE Rua Ébano 111 Térreo Rio Janeiro CEP 20930 060 RIL"

print(Sticker.sanitize(text))