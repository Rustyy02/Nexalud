FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# ✅ NO copiar el proyecto completo aquí (lo hace el volume)
# COPY . .

EXPOSE 8000

# ✅ Usar el mismo comando que en docker-compose
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# setup para superusuario
COPY scripts/setup_docker.sh /app/scripts/
RUN chmod +x /app/scripts/setup_docker.sh

# Comando que ejecuta migraciones Y crea superusuario
CMD ["sh", "-c", "python manage.py migrate && /app/scripts/setup_docker.sh && python manage.py runserver 0.0.0.0:8000"]