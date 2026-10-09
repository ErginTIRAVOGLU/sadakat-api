#!/bin/sh

echo "Veritabanının ayağa kalkması bekleniyor..."

# PostgreSQL'in TCP portunun dinlemeye başladığını basitçe kontrol edebiliriz 
# ya da doğrudan alembic komutunu çalıştırabiliriz (çünkü depends_on var ama postgres içi tam hazır olmayabilir)
# En garanti yol python ile bağlantı kontrolü yapmak veya kısa bir bekleme eklemektir:

until python -c "
import socket
s = socket.socket()
try:
    s.connect(('postgres', 5432))
    print('Veritabanı portu açık!')
except socket.error:
    exit(1)
" 2>/dev/null; do
  echo "PostgreSQL henüz hazır değil, bekleniyor..."
  sleep 1
done

echo "Alembic migrasyonları çalıştırılıyor..."
alembic upgrade head

echo "FastAPI başlatılıyor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload