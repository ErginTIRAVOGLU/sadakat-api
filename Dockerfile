# Resmi Python imajını temel alıyoruz
FROM python:3.11-slim

# Çalışma dizinini belirliyoruz
WORKDIR /app

# Sistem bağımlılıkları (gerekirse psycopg2 vb. kütüphaneler için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Önce gereksinim dosyasını kopyalayıp kütüphaneleri yüklüyoruz (önbellekleme optimizasyonu için)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje kodlarının geri kalanını kopyalıyoruz
COPY . .

# FastAPI'nin çalışacağı portu dışarıya bildiriyoruz
EXPOSE 8080

# Konteyner ayağa kalkınca FastAPI'yi Uvicorn ile başlatıyoruz
# (main.py içindeki app nesnesini hedefliyoruz)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]