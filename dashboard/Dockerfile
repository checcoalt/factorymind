# Immagine base
FROM python:3.11-slim

# Imposta la working directory
WORKDIR /app

# Copia tutti i file della dashboard
COPY . /app

# Installa dipendenze
RUN pip install --no-cache-dir \
    streamlit \
    pandas \
    numpy \
    pymongo \
    streamlit-option-menu

# Esponi la porta di Streamlit
EXPOSE 8501

# Comando di avvio
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
