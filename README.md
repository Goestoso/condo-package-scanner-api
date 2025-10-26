# Order Scanner API
API para extração de dados de moradores a partir de etiquetas de encomendas em condomínios, com validação automática contra o banco de dados de moradores.

## Descrição
Este projeto consiste em uma API que extrai informações de moradores (nome, endereço e complemento) a partir de imagens de etiquetas de encomendas. O pipeline realiza:

- OCR do texto da etiqueta (Tesseract)

- Detecção de entidades (NER spaCy) para nomes e endereços

- Sanitização e normalização de candidatos (remoção de stop tokens, números, romanos e abreviações de endereço)

- Validação de nomes e endereços com fuzzy matching usando dados reais do banco

- Validação opcional por unidade (apartamento/bloco) para filtrar resultados irrelevantes

## Tecnologias
- Python 3.13
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [spaCy](https://spacy.io) para NER
- [rapidfuzz](https://rapidfuzz.github.io/RapidFuzz) para fuzzy matching e normalização
- Logging integrado para debug e rastreamento

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

7. Configure a conexão com o banco de dados (no caso atual é o SQL Azure Server):

- Crie um arquivo chamado `db_connection.yml` dentro do diretório `configs/` e preencha-o com os dados abaixo (substitua os valores de exemplo pelos os valores reais de conexão do banco de dados):
```
# configs/db_connection.example.yml
server: condominio-server.database.windows.net
database: db-condominios-encomendas
username: admincondominio
password: sua_senha_aqui
driver: "{ODBC Driver 18 for SQL Server}"
encrypt: yes
trust_server_certificate: no
connection_timeout: 30
```

> 💡 Um arquivo `/configs/db_connection.example.yml` foi adicionado no projeto para auxiliar nessa etapa.

- Instale o driver ODBC para SQL Server caso não tenha instalado:
    - [Windows](https://learn.microsoft.com/pt-br/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver18)
    - [Linux (Unbutu/Debian)](https://learn.microsoft.com/pt-br/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver17&tabs=alpine18-install%2Calpine17-install%2Cdebian8-install%2Credhat7-13-install%2Crhel7-offline):
    - [macOS](https://learn.microsoft.com/pt-br/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-ver17)

- Para verificar se os valores do arquivo de conexão com o banco de dados estão certos, rode o comando abaixo (substitua os valores de exemplo do comando pelo os do arquivo de conexão):
```
sqlcmd -S condominio-server.database.windows.net -d db-condominios-encomendas -U admincondominio -P sua_senha_aqui -N -l 30
```
- Se a conexão for bem-sucedida, você verá um prompt `1>` aguardando comandos SQL.


## Estrutura do projeto
```
condo-package-scanner-api/
│
├─ assets/               # Imagens para teste
├─ configs/              # Configurações (normalização, logger, sanitização)
├─ data/                 # Datasets auxiliares
├─ models/               # Modelos NER treinados
├─ scripts/              # Scripts para atualização de datasets e modelos
├─ src/                  # Código-fonte principal
├─ tests/                # Testes unitários e integração
└─ CondoPackageScannerAPI     # Executável da API
```

## Treinamentos de modelos NER

O projeto permite treinar modelos NER do zero para nomes e endereços, assim como atualizar ou reforçar modelos já existentes usando fine-tuning.

### Treinamento do zero

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

### Atualização / Fine-Tuning de Modelos

O projeto permite atualizar modelos NER existentes de duas maneiras, dependendo do objetivo: ***fine-tuning para correção de erros específicos*** e ***atualização geral***.

> **💡 Dica**: Sempre teste o modelo atualizado em um conjunto de validação antes de colocar em produção. Ajustes nos scripts podem ser necessários dependendo do hardware, tamanho do dataset e estratégia de treinamento.

#### 1. Fine-Tuning para Correção de Erros Específicos (`update_fine_tuning_ner_model.py`)

- Objetivo: corrigir falhas específicas do modelo sem afetar o restante do conhecimento já aprendido.

- Passos:

1. Identificar os erros ou falhas do modelo atual (ex.: nomes ou endereços que não foram detectados corretamente).

2. Criar um dataset específico de fine-tuning (model_erros.json) contendo apenas os casos que precisam ser corrigidos.

3. Criar e executar o script de fine-tuning:
```
python scripts/update_fine_tuning_ner_model.py
```

- **Observação**: este processo mantém o conhecimento antigo do modelo e reforça áreas problemáticas.

#### 2. Atualização Geral com Novos Dados (`update_ner_model.py`)

- Objetivo: ensinar novos dados e estratégias ao modelo, expandindo seu conhecimento.

- Passos:

1. Atualizar os scripts de geração de datasets:
    - `generate_names.py`
    - `generate_address.py`

2. Atualizar datasets auxiliares, como:
    - `names_contexts`
    - `neighborhoods`
    - `cond_names`
    - `extra_words`

3. Executar o script de atualização geral:
```
python scripts/update_ner_model.py
```
- **Observação**: este processo amplia o modelo, incorporando novos dados e contextos, mas pode alterar o desempenho em exemplos antigos se não for feito com cuidado.

## Pipeline Completo de Extração

O pipeline de extração de dados funciona da seguinte forma:

1. **OCR com Tesseract**

- O texto é extraído da imagem da etiqueta usando o Tesseract OCR (`pytesseract`).

- Resultado: texto bruto contendo informações do destinatário.

2. **Pipeline de Normalização do Texto**

- Função `normalize_full` do módulo `normalize.py`.

- Padroniza maiúsculas/minúsculas, estados, CEPs, números (inclui romanos também) e complementos.

- Resultado: texto consistente e padronizado, pronto para NER.

3. **Pipeline de Sanitização do Texto**

- Função `sanitize_full` do módulo `sanitize.py`.

- Remove stopwords, códigos alfanuméricos, links e tokens irrelevantes.

- Resultado: texto limpo e filtrado, pronto para detecção de entidades.

4. **NER (Named Entity Recognition)**

- Modelos spaCy treinados detectam candidatos a nomes (`PERSON`) e endereços (`STREET`, `NUMBER`, `COMPLEMENT`, `CITY`, `STATE`).

- Resultado: lista de candidatos detectados em cada categoria.

- Se nenhum candidato for idenficado pelo NER, será necessário uma nova imagem com as informações necessárias mais nítidas.

5. **Validação Fuzzy** 

- Compara candidatos com moradores do banco de dados usando `rapidfuzz`.

- Limiar de similaridade padrão: **≥70**.

- Resultados múltiplos: seleciona o(s) mais próximo(s) do candidato NER.

6. **Validação por Unidade (Opcional)**

- Se bloco/apartamento identificados, restringe o fuzzy match apenas aos moradores daquela unidade, evitando resultados irrelevantes.

- Evita incluir nomes irrelevantes do texto da etiqueta.

- Pode usar fallback global se nenhum candidato for encontrado na unidade.


```
Resumo gráfico do fluxo:

Imagem da etiqueta
        │
        ▼
   Tesseract OCR
        │
        ▼
  Normalização + Sanitização
        │
        ▼
        NER
        │
        ▼
Fuzzy Match com moradores
        │
        ▼
Validação por unidade (opcional)
        │
        ▼
Atributos preenchidos

```

## Logging

O projeto utiliza logging para monitoramento do pipeline, debug e rastreamento de erros.

**Configuração**

- Níveis de log:
    - `DEBUG`: detalhes do pipeline (candidatos NER, fuzzy match, etc.)
    - `INFO`: progresso geral e resultados finais
    - `WARNING` / `ERROR`: avisos e erros críticos

- Configuração padrão grava logs no console, podendo ser ajustada para arquivos em `configs/logger_config.yml`.

**Uso nos módulos**

- **Sticker**: logs sobre extração de texto OCR (`DEBUG` / `INFO`).

- **Extractor**: logs detalhados sobre:
      - Normalização e sanitização
      - Entidades detectadas pelo NER
      - Resultados do fuzzy match e fallback
      - Definição final de recipient_name e recipient_address

**Exemplo de saída**
```
[INFO] OCR concluído: texto extraído da etiqueta
[DEBUG] Sanitize Pipeline: "Rua Ana 35 Carapicuiba SP"
[DEBUG] Candidatos detectados pelo Name NER: ["Mauricio de Souza"]
[INFO] Nome final detectado pelo NER + Fuzzy: Mauricio de Souza
[DEBUG] Candidatos de endereço detectados pelo NER: ["Rua Ana 35", "Carapicuiba", "SP"]
[INFO] Endereço final detectado pelo NER + Fuzzy: Rua Ana 35 Carapicuiba SP
```

**Observações**

- Mantenha `DEBUG` durante testes e ajustes de modelos."
- Em produção, utilize `INFO` ou `WARNING` para reduzir mensagens.
- Logs ajudam a identificar problemas no OCR, NER ou fuzzy match.

## Como Executar

> 💡 Antes de iniciar a execução da aplicação, siga as instruções de instalação mencionadas anteriormente.

Para executar a aplicação:

1. Adicione a imagem (preferencialmente no formato `.jpg`) de etiqueta de encomenda de condomínio (foque nos dados do morador para facilitar o processo) dentro do diretório `assets/`.
2. No código do ponto de entrada da aplicação, chamado `CondoPackageScannerAPI.py`, insira o nome do arquivo da imagem no trecho sinalizado abaixo:
```
if __name__ == '__main__':

    main("imagem_etiqueta.jpg") # <----- Insira o nome do arquivo da imagem no argumento da função main()
```
3. Execute o programa `CondoPackageScannerAPI.py` usando o _python_ via terminal:
```
python CondoPackageScannerAPI.py
```

4. Durante e após a execução do programa, algumas informações irão aparecer no console e no arquivo `.log`, conforme a configuração do arquivo `configs/logger_config.yml`, por exemplo:
```
2025-10-26 00:44:18 | src.main | INFO | Iniciando extração da imagem: correios.jpg
2025-10-26 00:44:18 | Extractor | INFO | Sticker criado para a imagem: /home/patton/Documents/tg/condo-package-scanner-api/assets/correios.jpg
2025-10-26 00:44:18 | Extractor | INFO | Carregando modelos NER...
2025-10-26 00:44:18 | Extractor | INFO | Modelos carregados com sucesso.
2025-10-26 00:44:18 | Extractor | INFO | OCR concluído. Texto extraído com 283 caracteres
2025-10-26 00:44:18 | src.main | INFO | OCR concluído.
2025-10-26 00:44:18 | Extractor | INFO | Candidatos a nomes extraídos: ['João Dias']
2025-10-26 00:44:18 | Extractor | INFO | Candidatos a endereços extraídos: {'STREET': ['Rua Jonas Fonseca'], 'NUMBER': ['01000', '1 m 112233', '250', 'Volume 1'], 'COMPLEMENT': ['Condominio Azul Apartamento Sao Goncalo'], 'CITY': ['Ii Condominio Nome Legivel Destinatario', 'Joao Dias', 'Pedido', 'Remotento Sigep Web Ambiente Homologacao'], 'STATE': []}
2025-10-26 00:44:18 | Extractor | INFO | Nenhum bloco ou apartamento identificado no endereço extraído.
2025-10-26 00:44:18 | src.db.odbc_api | INFO | Arquivo de configuração do banco carregado com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados 'db-condominios-encomendas' no servidor 'condominio-server.database.windows.net' estabelecida com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados encerrada com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Arquivo de configuração do banco carregado com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados 'db-condominios-encomendas' no servidor 'condominio-server.database.windows.net' estabelecida com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados encerrada com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Arquivo de configuração do banco carregado com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados 'db-condominios-encomendas' no servidor 'condominio-server.database.windows.net' estabelecida com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados encerrada com sucesso.
2025-10-26 00:44:24 | src.utils.validators | INFO | Nome 'João Dias' validado via LIKE único: Joao Dias
2025-10-26 00:44:24 | src.utils.validators | INFO | Buscando moradores do apartamento 672, bloco F
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Arquivo de configuração do banco carregado com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados 'db-condominios-encomendas' no servidor 'condominio-server.database.windows.net' estabelecida com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados encerrada com sucesso.
2025-10-26 00:44:24 | src.utils.validators | INFO | Nome 'Joao Dias' validado via fuzzy forte (>=70): {'Joao Dias'}
2025-10-26 00:44:24 | src.utils.validators | INFO | Validação por unidade concluída. Resultados: {'Joao Dias'}
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Arquivo de configuração do banco carregado com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados 'db-condominios-encomendas' no servidor 'condominio-server.database.windows.net' estabelecida com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados encerrada com sucesso.
2025-10-26 00:44:24 | src.utils.validators | INFO | Buscando moradores do apartamento 672, bloco F
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Arquivo de configuração do banco carregado com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados 'db-condominios-encomendas' no servidor 'condominio-server.database.windows.net' estabelecida com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados encerrada com sucesso.
2025-10-26 00:44:24 | src.utils.validators | INFO | Nome 'Joao Dias' validado via fuzzy forte (>=70): {'Joao Dias'}
2025-10-26 00:44:24 | src.utils.validators | INFO | Validação por unidade concluída. Resultados: {'Joao Dias'}
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Arquivo de configuração do banco carregado com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados 'db-condominios-encomendas' no servidor 'condominio-server.database.windows.net' estabelecida com sucesso.
2025-10-26 00:44:24 | src.db.odbc_api | INFO | Conexão com o banco de dados encerrada com sucesso.
2025-10-26 00:44:24 | src.main | INFO | Extração completa: {'names': ['Joao Dias'], 'unit_info': {'apartment': '672', 'block': 'F'}}
```

