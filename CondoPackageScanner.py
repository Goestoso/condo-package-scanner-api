"""
Executável do Condo Package Scanner para uso via linha de comando.
"""

import sys
from src.main import main

if __name__ == '__main__':
    # Checa se recebeu ao menos 1 argumento (imagem)
    if len(sys.argv) < 2:
        print("\n❌ ERRO: Caminho da imagem não informado.\n")
        print("Uso correto:")
        print("    python CondoPackageScanner.py <caminho_da_imagem>\n")
        print("Exemplo:")
        print("    python CondoPackageScanner.py ./assets/correios.jpg\n")
        sys.exit(1)

    caminho = sys.argv[1]
    
    result = main(caminho)

    print("\n===== RESULTADO =====")
    print(result)
