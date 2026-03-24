# 1. Usar una imagen oficial de Python ligera
FROM python:3.10-slim

# 2. TRUCO MÁGICO: Copiar 'uv' directamente desde su creador (Astral)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Establecer el directorio de trabajo
WORKDIR /app

# 4. Instalar dependencias del sistema operativo (necesarias para SQLite/Pandas)
RUN apt-get update && apt-get install -y gcc sqlite3 && rm -rf /var/lib/apt/lists/*

# 5. Copiar e instalar requerimientos usando UV
COPY requirements.txt .
# Usamos --system para que lo instale directamente en el Python del contenedor sin crear entornos virtuales extra
RUN uv pip install --system --no-cache -r requirements.txt

# 6. Copiar todo el código fuente
COPY . .

# 7. Crear la base de datos de prueba automáticamente al construir
RUN python scripts/seed_db.py

# 8. Exponer el puerto de Streamlit
EXPOSE 8501

# 9. Comando para ejecutar la app
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]