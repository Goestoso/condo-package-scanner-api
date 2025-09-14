import sys
from pathlib import Path

# Adiciona a pasta src ao sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Agora dá para importar o módulo
from sticker import Sticker

text = "Moldes Vestido Pet Nessas presa Destinatário Mauro Rua dos Pregos 476 Condomíno Apt 701 13431 112 São Paulo Remetente ueitom vitor lua Tiradentes casa Campos 37160 000 Minas Garais"

print(Sticker.sanitize(text))