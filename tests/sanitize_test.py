import sys
from pathlib import Path

# Adiciona a pasta src ao sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Agora dá para importar o módulo
import utils as utils

text = "Growth SUPPLEMENTS Contrato SPE Recebedor Assinatura DESTINATÁRIO PEDRO HENRIQUE PARIZOTI MEYER RUA IARA 476 PARQUE DOS CAMARGOS 06436 160 BARUERI Remetente GROWTH SUPPLEMENTS PRODUTOS ALIMENTÍCIOS LTDA AVENIDA WILSON LEMOS 2850 SANTA LUZIA 88200 958 TIJUCAS"

print(utils.full_pipeline(text))