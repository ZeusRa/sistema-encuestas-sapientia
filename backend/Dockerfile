FROM python:3.12.7

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar y instalar dependencias de Python
COPY requerimientos.txt .
RUN pip install --no-cache-dir -r requerimientos.txt

# El código se montará como volumen, pero copiamos por si acaso se construye sin volumen
COPY . .

# Comando para desarrollo con hot-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
