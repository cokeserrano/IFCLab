FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias necesarias para ifcopenshell
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requisitos primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorios de almacenamiento
RUN mkdir -p /tmp/ifc_uploads /tmp/modify_ifc && \
    chmod 777 /tmp/ifc_uploads /tmp/modify_ifc

# Exponer el puerto en el que se ejecutará la aplicación
EXPOSE $PORT

# Comando para ejecutar la aplicación con gunicorn
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8