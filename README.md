# Sadakat API

Sadakat API, müşteri sadakat programları, kampanyalar, ödül yönetimi ve iş yeri operasyonlarını destekleyen FastAPI tabanlı bir backend servisidir. İşletmeler için müşteri kazanım, ödül dağıtımı, QR tabanlı etkileşim ve müşteri sadakat takibi gibi iş akışlarını yönetir.

## Özellikler

- Kullanıcı kimlik doğrulama ve yetkilendirme
- Müşteri ve işletme hesabı kayıt akışları
- İşletme profili ve çalışan yönetimi
- Kampanya oluşturma ve yönetimi
- QR oturumları ve müşteri etkileşimi
- Ödül sistemi ve ödül talep akışı
- Müşteri dashboard görünümü
- İşlem ve sadakat kart takibi
- PostgreSQL + Redis destekli asenkron arka uç
- Swagger/OpenAPI otomatik dokümantasyon desteği

## Teknoloji Yığını

- Python 3.12
- FastAPI
- SQLAlchemy (Async)
- PostgreSQL
- Redis
- Alembic
- Pydantic + Pydantic Settings
- JWT tabanlı kimlik doğrulama
- Docker / Docker Compose

## Proje Yapısı

```text
sadakat-api/
├── app/
│   ├── auth/
│   ├── businesses/
│   ├── campaigns/
│   ├── common/
│   ├── core/
│   ├── customer_dashboard/
│   ├── customer_rewards/
│   ├── loyalty_cards/
│   ├── qr_sessions/
│   ├── reward_claims/
│   ├── rewards/
│   ├── stamps/
│   ├── transactions/
│   ├── users/
│   ├── main.py
│   └── models.py
├── alembic/
├── .env2.local
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── pyproject.toml
├── requirements.txt
├── README.md
├── alembic.ini
└── .env
```

## Gereksinimler

- Python 3.12+
- PostgreSQL
- Redis
- Docker (isteğe bağlı)
- pip

## Çalıştırma

### 1) Depoyu klonlayın

```bash
git clone https://github.com/ErginTIRAVOGLU/sadakat-api.git
cd sadakat-api
```

### 2) Sanal ortam oluşturun

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3) Bağımlılıkları yükleyin

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Ortam değişkenlerini hazırlayın

Proje kökünde `.env` dosyası oluşturun:

```env
APP_NAME=Fidelza API
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+asyncpg://fidelza:fidelza_password@localhost:5432/fidelza
REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

Not: `docker-compose.yml` içinde PostgreSQL ve Redis servisleri otomatik olarak tanımlanmıştır. Yerel çalıştırma için yerel servislerin açık olması gerekir.

### 5) Veritabanı migrasyonlarını çalıştırın

```bash
alembic upgrade head
```

### 6) Uygulamayı başlatın

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Uygulama açıldığında aşağıdaki adreslerden erişilebilir:

- API: http://localhost:8080
- Swagger: http://localhost:8080/docs
- Redoc: http://localhost:8080/redoc

## Docker ile Çalıştırma

Projede hazırlanan `docker-compose.yml` ile tüm servisleri tek komutla başlatabilirsiniz:

```bash
docker compose up --build
```

Bu komut şu servisleri başlatır:

- FastAPI uygulaması
- PostgreSQL
- Redis

Servisler içindeki `entrypoint.sh` betiği, veritabanı erişimi hazır olana kadar bekler ve ardından Alembic migrasyonlarını çalıştırıp Uvicorn sunucusunu başlatır.

## API ve Sağlık Kontrolleri

Uygulama içinde temel sağlık kontrolü ve veritabanı/Redis kontrolleri tanımlıdır:

- `GET /health`
- `GET /health/db`
- `GET /health/redis`

## Önemli Notlar

- `app/core/config.py` dosyası `.env` dosyasını otomatik olarak okur.
- SQLAlchemy async motoru `app/core/database.py` içinde tanımlıdır.
- Redis bağlantısı `app/core/redis.py` üzerinden yönetilir.
- Tüm endpointler `app/main.py` içinde include edilir.

## Geliştirme
 

### Kod formatı ve lint

```bash
ruff check .
```

## Lisans

Bu proje için özel lisans bilgisi belirtilmemiştir. Kullanım öncesinde repository sahibiyle doğrulama yapılması önerilir.

## Katkı

Katkı yapmak isterseniz:

1. Fork oluşturun
2. Feature branch açın
3. Değişikliklerinizi yapın
4. Pull request gönderin

## İletişim

Proje sahibi veya ekibin iletişim bilgilerine repository sayfasından ulaşabilirsiniz.
