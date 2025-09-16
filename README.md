# Order Scanner API
API para extração de dados de moradores a partir de etiquetas de encomendas

## Descrição
Este projeto consiste em uma API que extrai informações de moradores (como nome, endereço e complemento) a partir de imagens de etiquetas de encomendas em condomínios.
O pipeline utiliza OCR (Tesseract) para reconhecimento de texto, NER (spaCy) para identificar nomes e endereços, e rapidfuzz para correção e normalização de dados.
## Tecnologias
- Python 3.13
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [spaCy](https://spacy.io) para NER
- [rapidfuzz](https://rapidfuzz.github.io/RapidFuzz) para fuzzy matching e normalização

## Instalação 
1. Clone o repositório:

```
git clone https://github.com/seu-usuario/order-scanner-api.git
cd order-scanner-api
```

2. Crie e ative um ambiente virtual:
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```
pip install -r requirements.txt
```

4. Instale o Tesseract OCR:
- Windows: [Download do instalador](https://github.com/tesseract-ocr/tessdoc/blob/main/Downloads.md#binaries-for-windows) (certifique-se de adicionar o caminho do Tesseract ao PATH do sistema).

- Linux Ubuntu/Debian (mais recomendável por ser mais recente):
```
sudo apt install tesseract-ocr
```

5. Configure o idioma `pt-br` no Tesseract OCR:
- Windows: Durante a instalação, selecione o idioma `Portuguese` (ou baixe o pacote de idiomas separado, se necessário).
- Linux Unbutu/Debian:
```
sudo apt install tesseract-ocr-por
```

6. Testando a instalação do Tesseract OCR:

- No terminal, execute:
```
tesseract --version
```
- E para testar a extração em português:
```
tesseract imagem.jpg saida.txt -l por
```

## Estrutura do projeto
```
order-scanner-api/
│
├─ assets/               # Imagens usadas para OCR e testes
├─ configs/              # Configurações de nomes e endereços para treinar NER
├─ data/                 # Datasets de treinamento e auxiliares
├─ models/               # Modelos NER treinados
├─ scripts/              # Scripts para gerar datasets e atualizar modelos
├─ src/                  # Código-fonte principal do projeto
├─ tests/                # Testes unitários
└─ order_scanner_api     # Executável da API
```

## Treinamentos de modelos NER
O projeto permite treinar modelos NER do zero para nomes e endereços.

**Pontos importantes**:

- Para acelerar o treinamento, é possível utilizar GPU NVIDIA via CUDA.

- É necessário instalar os drivers da NVIDIA e o software [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit?utm_source=chatgpt.com) compatível com sua GPU.

- Instale as dependências para GPU (escolha a versão do `cupy-cuda` compatível com a sua GPU):
```
pip install -U spacy thinc
pip install cupy-cuda13x==13.6.0
```
> **Observação**: O uso de CUDA não é obrigatório. O treinamento pode ser feito na CPU, embora seja mais lento.

- Treinamento do modelo do zero:
```
python -m spacy train configs/model_config.cfg --output models/model_ner --gpu-id 0
```
- `configs/name_config.cfg`: arquivo de configuração do spaCy para o modelo NER de nomes.

- `--output models/name_ner`: diretório onde o modelo treinado será salvo.

- `--gpu-id 0`: ID da GPU a ser utilizada (opcional; remova ou use `--gpu-id -1` para CPU).
