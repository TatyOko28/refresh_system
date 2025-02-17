FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installer les dépendances système
RUN apt-get update && \
    apt-get install -y postgresql-client libpq-dev gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Installer pip et whitenoise
RUN pip install --upgrade pip
RUN pip install whitenoise

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier les fichiers du projet
COPY . .

# Exposer le port
EXPOSE 8000

# Lancer l'application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
