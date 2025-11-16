FROM python:3.11-slim

# Variável de ambiente para evitar buffering no log
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho no container
WORKDIR /app

# Dependências de sistema básicas
RUN apt-get update && apt-get install -y \
    unixodbc unixodbc-dev curl gnupg apt-transport-https build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala o driver ODBC 18 (para SQL Server)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

# 🧠 Instala Tesseract OCR (com suporte ao idioma português)
RUN apt-get update && apt-get install -y \
    tesseract-ocr libtesseract-dev tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# Define o caminho dos dados do Tesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Copia dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia apenas o essencial
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
