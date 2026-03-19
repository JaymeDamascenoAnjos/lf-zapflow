FROM python:3.10-slim

# Instala o ffmpeg (essencial para o pydub/whisper processar os áudios da perfumaria)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Define o diretório raiz como ponto de trabalho
WORKDIR .

# Copia e instala as dependências primeiro (aproveita o cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto para o diretório atual
COPY . .

# Garante que as pastas de banco de dados existam para o SQLite/JSON
RUN mkdir -p app/db/messages app/logs

# Porta padrão que o Render espera
EXPOSE 10000

# Comando para iniciar o FastAPI (Webhook)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
