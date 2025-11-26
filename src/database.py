#Veritabanı işlemleri

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine #fonksiyonu, bir veritabanı bağlantısı (database engine) oluşturur.
from sqlalchemy.ext.declarative import declarative_base #çağrıldığında bir Base sınıfı döner; bu sınıf, tüm ORM modellerinin (yani veritabanı tablolarını temsil eden Python sınıflarının) temeli olur.
from sqlalchemy.orm import sessionmaker #sayesinde veritabanına veri ekleme, silme, güncelleme gibi işlemler yapılır.

# .env dosyasından environment variables'ları yükle
load_dotenv()

# DATABASE_URL'i .env'den al, yoksa SQLite kullan (fallback)
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./src/veritabani.db")

# PostgreSQL için optimize edilmiş engine ayarları
if DB_URL.startswith("postgresql"):
    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,        # Bağlantı sağlığını kontrol et
        pool_size=10,               # Connection pool boyutu
        max_overflow=20,            # Maksimum ekstra bağlantı
        pool_recycle=3600,          # 1 saatte bağlantıları yenile
        echo=False                  # SQL loglarını kapat (production için)
    )
else:
    # SQLite için (local test)
    engine = create_engine(DB_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False) #Veritabanı için oturum açıldı. Veritabanı değişiklikleri commit edilmeden SQL gönderilmesin diye parametre False yapıldı.
Base = declarative_base() #SQLAlchemy'de ORM modellerini tanımlamak için temel (base) sınıfı oluşturur.

def get_db(): #Burada veritabanı oturumu try-yield ile açılır ve işlem bitince finally ile oturumu kapatır.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()