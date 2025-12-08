import sys
from pathlib import Path

# Adiciona a pasta src ao sys.path
sys.path.append(str(Path(__file__).parent.parent))

# Agora dá para importar o módulo
from src.utils import sanitize
from src.utils import normalize

text = "autorizacao Uso protocolo Simplific Rodovia PR Animais MG Ado PI 395 SE 9 Emissao Destinatario SP Cliente Sarah Olive Rua Xv Novembro 500 Bloco 2 Apartamento 12 Jardim Gabr Jandira SP Condominio Tel Mega Rota PB Mm Nto Sar SP Not"

text = normalize.normalize_full(text)
print(sanitize.sanitize_full(text))