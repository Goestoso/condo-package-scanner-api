FROM python:3.11-slim

# Variável de ambiente para evitar buffering no log
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho no container
WORKDIR /app

# Dependências de sistema básicas
RUN apt-get update && apt-get install -y \
    build-essential curl libmariadb-dev libmariadb-dev-compat \
    tesseract-ocr libtesseract-dev tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# Define o caminho dos dados do Tesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Copia dependências Python
COPY requirements.txt . 

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY src ./src
COPY configs ./configs
COPY models ./models
COPY data/sanitize ./data/sanitize
COPY server.py ./

# Cria diretório de logs
RUN mkdir -p logs

# Expõe a porta do servidor
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
