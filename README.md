# Order Scanner API
API (Interface de Programação de Aplicativos, ou, em inglês, _Application Programming Interface_) para extração de dados de moradores a partir de etiquetas de encomendas em condomínios, com validação automática contra o banco de dados de moradores.

## Descrição
Este projeto consiste em uma API que extrai informações de moradores (nome, endereço e complemento) a partir de imagens de etiquetas de encomendas. O pipeline realiza:

- OCR do texto da etiqueta (**Tesseract**)

- Detecção de entidades (NER **spaCy**) para nomes e endereços

- Sanitização e normalização de candidatos (remoção de stop tokens, números, romanos e abreviações de endereço)

- Validação de nomes e endereços com _fuzzy matching_ usando dados reais do banco

- Validação opcional por unidade (apartamento/bloco) para filtrar resultados irrelevantes

## Tecnologias
- Python 3.13
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract), como o próprio nome já indica (Reconhecimento Óptico de Caracteres, ou, em inglês, _Optical Character Recognition_), fará o reconhecimento óptico de caracteres (extração de texto contido especialmente em arquivos que são baseados em imagem, como `pdf`, `jpg`, `png`, etc)
- [spaCy](https://spacy.io), usará inteligência artificial para NER (Reconhecimento de Entidade Nomeada, ou, em inglês, _Named Entity Recognition_)
- [rapidfuzz](https://rapidfuzz.github.io/RapidFuzz) para fuzzy matching e normalização
- [FastAPI](https://fastapi.tiangolo.com) para construir a API do projeto
- [Uvicorn](https://uvicorn.dev), servidor ASGI (Interface de Gateway de Servidor Assíncrono, ou, em inglês, _Asynchronous Server Gateway Interface_) que executará a aplicação **FastAPI**
- [SQL Azure Database](https://learn.microsoft.com/pt-br/azure/azure-sql/database/sql-database-paas-overview?view=azuresql) é o serviço de banco de dados totalmente gerenciado, oferecido pela **Microsoft**, que armazenará as informações dos moradores e de suas respectivas encomendas
- [MySQL Database](https://www.mysql.com/about) é um sistema de gerenciamento de banco de dados relacional (RDBMS) de código aberto, que também pode ser usado para armazenar as informações dos moradores e de suas respectivas encomendas
- [Docker](https://docs.docker.com) é uma plataforma de código aberto que permite aos desenvolvedores construir, distribuir e executar aplicações de forma isolada dentro de "contêineres", como a API do projeto atual
- Logging integrado para debug e rastreamento

## Instalação 
1. Clone o repositório:

```
git clone https://github.com/seu-usuario/cond-package-scanner-api.git
cd condo-package-scanner-api
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

5. Configure o idioma `pt-br` no **Tesseract OCR**:
- Windows:
    - Durante a instalação, selecione o idioma `Portuguese` (ou baixe o pacote de idiomas separado, se necessário).
- Linux Unbutu/Debian:
```
sudo apt install tesseract-ocr-por
```

6. Testando a instalação do **Tesseract OCR**:

- No terminal, execute:
```
tesseract --version
```
- E para testar a extração em português:
```
tesseract imagem.jpg saida.txt -l por
```

7. Configure a conexão com o banco de dados:

- Crie um arquivo chamado `db_connection.yml` dentro do diretório `configs/` e preencha-o com os dados seguindo a estrtura do banco a ser usado:

> **SQL Azure Database**:

```
# configs/db_connection.example.yml
server: condominio-server.database.windows.net
database: db-condominios-encomendas
username: seu_usuario
password: sua_senha_aqui
driver: "{ODBC Driver 18 for SQL Server}"
encrypt: yes
trust_server_certificate: no
connection_timeout: 30
```

- Também instale o driver ODBC para SQL Server (caso não tenha instalado):
    - [Windows](https://learn.microsoft.com/pt-br/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver18)
    - [Linux (Unbutu/Debian)](https://learn.microsoft.com/pt-br/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver17&tabs=alpine18-install%2Calpine17-install%2Cdebian8-install%2Credhat7-13-install%2Crhel7-offline):
    - [macOS](https://learn.microsoft.com/pt-br/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-ver17)

- Para verificar se os valores do arquivo de conexão com o seu banco de dados estão certos, rode o comando abaixo (substitua os valores de exemplo do comando pelo os do arquivo de conexão):
```
sqlcmd -S condominio-server.database.windows.net -d db-condominios-encomendas -U admincondominio -P sua_senha_aqui -N -l 30
```
- Se a conexão for bem-sucedida, você verá um prompt `1>` aguardando comandos SQL.

> **MySQL Database**:

```
# host: shortline.proxy.rlwy.net
# port: 20562
# database: db_condominios_encomendas
# username: seu_usuario
# password: sua_senha_aqui
# connection_timeout: 30
```

> 💡 Um arquivo `/configs/db_connection.example.yml` foi adicionado no projeto para auxiliar nessa etapa (substitua os valores dos exemplos pelos valores reais de conexão do seu banco de dados).


## Estrutura do projeto
```
condo-package-scanner-api/
│
├─ assets/               # Imagens para teste
├─ configs/              # Configurações (normalização, logger, conexão com o banco)
├─ data/                 # Datasets auxiliares e stop words\tokens para sanitização
├─ docker/               # Dockerfiles para ambientes Azure ou MySQL
├─ models/               # Modelos NER treinados
├─ scripts/              # Scripts para atualização de datasets e modelos
├─ src/                  # Código-fonte principal
├─ tests/                # Testes unitários e integração
├─ server.py                # Onde está definido a aplicação FastAPI que rodará pelo servidor Uvicorn
└─ CondoPackageScanner.py     # Executável
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

- O texto é extraído da imagem da etiqueta usando o **Tesseract OCR** (`pytesseract`).

- Resultado: texto bruto contendo informações do destinatário.

2. **Pipeline de Normalização do Texto**

- Função `normalize_full` do módulo `normalize.py`.

- Padroniza maiúsculas/minúsculas, estados, CEPs, números (inclui romanos também) e complementos.

- Resultado: texto consistente e padronizado, pronto para **NER**.

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

- Mantenha `DEBUG` durante testes e ajustes de modelos.
- Em produção, utilize `INFO` ou `WARNING` para reduzir mensagens.
- Logs ajudam a identificar problemas no OCR, NER ou fuzzy match.

## Como Executar

> 💡 Antes de iniciar a execução, siga as instruções de instalação mencionadas anteriormente.

### Usando `CondoPackageScanner.py` (▶️ Executável)

Para executar a aplicação:

1. Baixe a imagem da etiqueta de condomínio
2. Execute o programa `CondoPackageScannerAPI.py` usando o _python_ via terminal passando o caminho da imagem como argumento, por exemplo:
```
python CondoPackageScanner.py .\assets\correios.jpg
```

3. Durante e após a execução do programa, algumas informações irão aparecer no console e no arquivo `.log`, conforme a configuração do arquivo `configs/logger_config.yml`, por exemplo:
```
2025-11-17 00:05:11 | src.main | INFO | Iniciando App...
2025-11-17 00:05:11 | Extractor | INFO | Sticker criado para a imagem: ./assets/correios.jpg
2025-11-17 00:05:11 | Extractor | INFO | Carregando modelos NER...
2025-11-17 00:05:12 | Extractor | INFO | Modelos carregados com sucesso.
2025-11-17 00:05:12 | Extractor | INFO | OCR concluído (283 caracteres)
2025-11-17 00:05:12 | Extractor | INFO | Candidatos a nomes extraídos: ['João Dias']
2025-11-17 00:05:12 | Extractor | INFO | Candidatos a endereços extraídos: {'STREET': ['Rua Jonas Fonseca'], 'NUMBER': ['01000', '1 m 112233', '250', 'Volume 1'], 'COMPLEMENT': ['Condominio Azul Apartamento Sao Goncalo'], 'CITY': ['Ii Condominio Nome Legivel Destinatario', 'Joao Dias', 'Pedido', 'Remotento Sigep Web Ambiente Homologacao'], 'STATE': []}
2025-11-17 00:05:12 | Extractor | INFO | Nenhum bloco ou apartamento identificado no endereço extraído.
2025-11-17 00:05:12 | src.utils.config_loader | INFO | Configuração do banco carregada com sucesso (SQLSERVER)
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server estabelecida com sucesso.
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server encerrada.
2025-11-17 00:05:12 | src.utils.config_loader | INFO | Configuração do banco carregada com sucesso (SQLSERVER)
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server estabelecida com sucesso.
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server encerrada.
2025-11-17 00:05:12 | src.utils.config_loader | INFO | Configuração do banco carregada com sucesso (SQLSERVER)
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server estabelecida com sucesso.
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server encerrada.
2025-11-17 00:05:12 | src.utils.validators | INFO | Nome 'João Dias' validado via LIKE único: Joao Dias
2025-11-17 00:05:12 | src.utils.validators | INFO | Buscando moradores do apartamento 672, bloco F
2025-11-17 00:05:12 | src.utils.config_loader | INFO | Configuração do banco carregada com sucesso (SQLSERVER)
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server estabelecida com sucesso.
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server encerrada.
2025-11-17 00:05:12 | src.utils.validators | INFO | Nome 'Joao Dias' validado via fuzzy forte (>=70): {'Joao Dias'}
2025-11-17 00:05:12 | src.utils.validators | INFO | Validação por unidade concluída. Resultados: {'Joao Dias'}
2025-11-17 00:05:12 | src.utils.config_loader | INFO | Configuração do banco carregada com sucesso (SQLSERVER)
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server estabelecida com sucesso.
2025-11-17 00:05:12 | src.db.sqlserver_api | INFO | Conexão SQL Server encerrada.
2025-11-17 00:05:12 | src.main | INFO | Encerrando App...

===== RESULTADO =====
{'candidates': 1, 'names_with_units_info': {'Joao Dias': {'apartment': '672', 'block': 'F'}}, 'reason': 'Candidato único validado no banco de dados'}
```

### Usando `server.py` (🌐 Servidor)

- Para iniciar o servidor, rode o comando (no diretório do projeto) via terminal:
```
uvicorn server:app --reload
```
> Isso irá executar o programa `server.py` (onde está definida a aplicação **FastAPI**) usando o servidor **Uvicorn**.

- Para parar o servidor:
    - Pressione as teclas `Ctrl` + `C`

 - Os retornos seguirão o seguinte padrão em caso de **sucesso**:
```
{
  "status": "success",
  "data": {
    "candidates": int,
    "names_with_units_info": {
      "name1": {"apartment": str, "block": str},
      "name2": {"apartment": str, "block": str},
      ...
      },
    "reason": str
    }
  }
}
```

- Os retornos seguirão o seguinte padrão em caso de **erro**:

```
{
  "status": "error",
  "data": {
    "message": str,
    "traceback": str
  }
}
```

> 📝 Para mais detalhes, acesse a documentação interativa da API (**Swagger UI**) que ficará disponível em `http://localhost:8000/docs` após o servidor entrar em execução.

### Usando `Docker` (📦 Container)

A aplicação pode ser executada facilmente dentro de um container Docker, sem a necessidade de instalar manualmente dependências como Python, drivers ODBC ou Tesseract OCR. 

- 💡 Os comandos do **Docker** com `sudo` só são necessários se for rodar no sistema operacional **Linux (Debian/Ubuntu)**, para rodar em **Docker Desktop** no **Windows** ou  **macOS** basta copiar os comandos e apagar o `sudo` deles.

Siga os passos abaixo:

> 🧰 **1. Instalar o Docker**

Caso ainda não tenha o Docker instalado, siga as instruções oficiais de acordo com seu sistema operacional:

- **Linux (Debian/Ubuntu)**:
```
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl start docker
```

Para verificar se está funcionando:
```
docker run hello-world
```
- **Windows / macOS**:
    - Baixe e instale o [Docker Desktop](https://www.docker.com/products/docker-desktop)
    - Após a instalação, abra o terminal integrado do Docker Desktop e teste:
      
```
docker run hello-world
```

> 🏗️ **2. Criar a imagem da aplicação**

No diretório do projeto onde está o arquivo `Dockerfile` (`/docker/mysql/` ou `/docker/azure/`, escolha conforme o tipo de conexão com o banco de dados a ser usada), execute o comando abaixo para construir a imagem Docker da API (os exemplos serão com a conexão **Azure**):
```
sudo docker build -t condo-package-scanner-api:azure-v1 -f ./docker/azure/Dockerfile .
```

Esse processo pode demorar alguns minutos, pois ele:

- Baixa a imagem base do Python.

- Instala dependências do sistema (ODBC, Tesseract, etc.).

- Copia o código da aplicação para dentro do container.

Ao finalizar, você verá uma mensagem semelhante a:
```
Successfully tagged condo-package-scanner-api:lates
```

> 🚀 **3. Executar o container**

Depois da imagem criada, rode o container com o comando:

```
docker run -d \                                                                                                                                                         
  --name condo-api-azure \
  -p 8000:8000 \
  condo-package-scanner-api:azure-v1
```

- Esse comando:
    - Inicia o container em modo “**detached**” (em segundo plano);
    - Faz o **mapeamento da porta 8000** do container para a porta 8000 local, permitindo acessar a API via navegador ou Postman;
    - Nomeia o container como `condo-api-azure`.

- 💡 Caso já exista um container com esse nome, remova-o antes de recriar:
```
sudo docker rm -f condo-api-azure
```

- 👁️ Para verificar se o container está em execução:
```
docker ps
```
Aparecerá uma mensagem semelhante a essa:
```
CONTAINER ID   IMAGE                                  COMMAND                  CREATED         STATUS         PORTS                                         NAMES
6db7728ca467   condo-package-scanner-api:azure-v1   "uvicorn server:app …"   4 seconds ago   Up 3 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp   condo-api-azure
```

> 🧩 **4. Acessar a API**

Após o container estar em execução, a API estará disponível em:

👉 http://localhost:8000

Você pode testar diretamente os endpoints no navegador ou ferramentas como Insomnia ou Postman.


- A documentação interativa da API (**Swagger UI**) estará disponível em:

🔗 http://localhost:8000/docs

> 📊 **5. Ver logs da aplicação**

Para visualizar os logs em tempo real:
```
sudo docker logs -f condo-api-azure
```

Isso mostrará as mensagens de inicialização, processamento de OCR, consultas ao banco, etc.

> 🛑 **6. Parar e remover o container**

Para parar o container :
```
sudo docker stop condo-api-azure
```

Para removê-lo completamente:
```
sudo docker rm condo-api-azure
```

> ♻️ **7. Atualizar a imagem**

Se você fizer alterações no código da aplicação, basta reconstruir a imagem com:
```
sudo docker build -t condo-package-scanner-api:azure-v1 -f ./docker/azure/Dockerfile .
```

E reiniciar o container:
```
sudo docker rm -f condo-api-azure
sudo docker run -d \                                                                                                                                                         
  --name condo-api-azure \
  -p 8000:8000 \
  condo-package-scanner-api:azure-v1
```
