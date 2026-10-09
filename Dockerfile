# Resmi Python imajını temel alıyoruz
FROM python:3.12-slim

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

# Entrypoint betiğine çalıştırma izni veriyoruz
RUN chmod +x entrypoint.sh

# FastAPI'nin çalışacağı portu dışarıya bildiriyoruz
EXPOSE 8080

# Konteyner ayağa kalkarken doğrudan entrypoint çalışacak
ENTRYPOINT ["./entrypoint.sh"]