# 🔐 Secure Social Media Platform

Yapay zeka destekli içerik moderasyonu ve kimlik doğrulama sistemi ile güvenli sosyal medya platformu.

## ✨ Özellikler

### 🛡️ Güvenlik ve Doğrulama
- **Kimlik Kartı Okuma**: OCR ve yüz tanıma teknolojisi ile otomatik kayıt
- **Kart ile Giriş**: Görüntü eşleştirme algoritması ile güvenli giriş
- **JWT Authentication**: Token tabanlı güvenli oturum yönetimi

### 🤖 Yapay Zeka Moderasyonu
- **Görsel İçerik Kontrolü**: CLIP-ViT modeli ile 36 etiketli analiz sistemi
  - Şiddet/Kan içerik tespiti
  - Uygunsuz içerik tespiti
  - Silah ve tehdit içeriği tespiti
  - Nefret söylemi tespiti
  - 20 güvenli "decoy" etiket ile yanlış pozitif önleme
- **Metin Moderasyonu**: Transformers tabanlı Türkçe küfür/hakaret algılama
- **OCR Kontrolü**: Görsellerdeki yazılardan uygunsuz içerik tespiti

### 📱 Sosyal Özellikler
- Görsel ve metin paylaşımı
- Beğeni sistemi
- Takip/takipçi sistemi
- Hashtag arama
- Kullanıcı profilleri
- Aktivite akışı

### 🎨 Kullanıcı Arayüzü
- Modern dark mode tasarım
- Responsive mobil uyumlu
- Glassmorphism efektleri
- Smooth animasyonlar

## 🏗️ Teknoloji Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy
- **Authentication**: JWT (python-jose)
- **AI Models**:
  - CLIP-ViT-base-patch32 (Görsel analiz)
  - Transformers (Metin analiz)
  - EasyOCR (Türkçe/İngilizce OCR)
  - MTCNN (Yüz tanıma)

### Frontend
- **Framework**: Astro v4.16.17 (SSR)
- **UI Library**: React + TypeScript
- **Styling**: Custom CSS (Dark theme)
- **State Management**: LocalStorage

### AI & Computer Vision
- **Content Moderation**: OpenAI CLIP model
- **Text Moderation**: Turkish NLP model
- **Face Detection**: MTCNN
- **OCR**: EasyOCR
- **Card Matching**: ORB feature detection + BFMatcher

## 📦 Kurulum

### Gereksinimler
- Python 3.11+
- Node.js 18+
- PostgreSQL database (Supabase önerilir)

### 1. Backend Kurulumu

```bash
# Virtual environment oluştur
python -m venv env

# Aktif et (Windows)
env\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Environment variables ayarla
# .env dosyası oluştur ve şu değişkenleri ekle:
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key-here

# Veritabanı tablolarını oluştur (otomatik)
uvicorn src.main:app --reload
```

### 2. Frontend Kurulumu

```bash
cd frontend

# Bağımlılıkları yükle
npm install

# Development server başlat
npm run dev
```

### 3. Erişim

- Backend API: http://127.0.0.1:8000
- Frontend: http://localhost:3000
- API Docs: http://127.0.0.1:8000/docs

## 📁 Proje Yapısı

```
BitirmeProjesi/
├── src/                          # Backend kaynak kodu
│   ├── ai/                       # AI/ML modülleri
│   │   ├── card_reader.py        # Kimlik kartı OCR sistemi
│   │   ├── card_matcher.py       # Kart eşleştirme algoritması
│   │   ├── content_moderator.py  # CLIP görsel moderasyon
│   │   └── text_moderator.py     # Metin moderasyon
│   ├── auth/                     # Authentication
│   │   ├── models.py             # User, Follow modelleri
│   │   ├── schemas.py            # Pydantic şemaları
│   │   ├── service.py            # Business logic
│   │   └── views.py              # API endpoints
│   ├── post/                     # Post yönetimi
│   │   ├── models.py             # Post, Hashtag modelleri
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── views.py
│   ├── profile/                  # Profil yönetimi
│   ├── activity/                 # Aktivite sistemi
│   ├── database.py               # Database bağlantısı
│   ├── api.py                    # Router yapılandırması
│   └── main.py                   # FastAPI app
├── frontend/                     # Frontend kaynak kodu
│   ├── src/
│   │   ├── components/           # React bileşenleri
│   │   │   ├── Feed.tsx          # Ana akış
│   │   │   └── Profile.tsx       # Profil sayfası
│   │   ├── pages/                # Astro sayfaları
│   │   │   ├── index.astro       # Landing page
│   │   │   ├── login.astro       # Giriş
│   │   │   ├── signup.astro      # Kayıt
│   │   │   └── feed.astro        # Ana sayfa
│   │   ├── lib/
│   │   │   ├── api.ts            # API client
│   │   │   └── config.ts         # Yapılandırma
│   │   └── layouts/
│   └── public/                   # Statik dosyalar
├── requirements.txt              # Python bağımlılıkları
├── .env                          # Environment variables (Git'te yok)
├── .gitignore
└── README.md
```

## 🔑 API Endpoints

### Authentication
- `POST /v1/auth/read-card` - Kimlik kartı okuma
- `POST /v1/auth/signup` - Kullanıcı kaydı
- `POST /v1/auth/login` - Email/username ile giriş
- `POST /v1/auth/login-with-card` - Kart ile giriş
- `GET /v1/auth/profile` - Profil bilgisi
- `PUT /v1/auth/{username}` - Profil güncelleme
- `DELETE /v1/auth/{username}` - Hesap silme

### Posts
- `POST /v1/posts/` - Yeni gönderi (AI moderasyon)
- `GET /v1/posts/feed` - Ana akış
- `GET /v1/posts/user/{username}` - Kullanıcı gönderileri
- `GET /v1/posts/hashtag/{hashtag}` - Hashtag arama
- `DELETE /v1/posts/` - Gönderi silme
- `POST /v1/posts/like` - Beğenme
- `POST /v1/posts/unlike` - Beğenmeden vazgeçme

### Profile
- `GET /v1/profile/user/{username}` - Profil görüntüleme
- `POST /v1/profile/follow/{username}` - Takip et
- `POST /v1/profile/unfollow/{username}` - Takipten çık
- `GET /v1/profile/followers` - Takipçiler
- `GET /v1/profile/following` - Takip edilenler

### Activity
- `GET /v1/activity/user/{username}` - Kullanıcı aktiviteleri

## 🛡️ Content Moderation Detayları

### Görsel Moderasyon (36 Etiket)
**Yasaklı Kategoriler (16 etiket):**
- **Grup A (Şiddet/Kan)**: Physical violence, blood, corpse, car accident, torture
- **Grup B (-)**: -
- **Grup C (Silah)**: Firearm, knife, drugs, terrorist
- **Grup D (Nefret)**: Middle finger, hate symbols

**Güvenli Decoy Etiketler (20 etiket):**
- Kırmızı objeler (araba, gül, boya, elbise, et) - Kan algılamasını iyileştirir
- Siyah objeler (telefon, cüzdan, kumanda) - Silah false positive önleme
- Fiziksel temas (sarılma, spor, emzirme) - Şiddet false positive önleme
- Plaj/spor kıyafetleri - NSFW false positive önleme

### Metin Moderasyon
- Türkçe küfür/hakaret algılama
- Saldırgan dil tespiti
- Nefret söylemi analizi
- OCR ile görsellerdeki yazı kontrolü

### Hata Mesajları
Her ihlal için detaylı, yapılandırılmış hata mesajları:
- 🚫 Emoji başlıklar
- Tespit edilen kategori
- Güven oranı (%)
- ⚠️ Madde işaretli açıklamalar
- Kullanıcı dostu öneriler

## 🔒 Güvenlik Özellikleri

- ✅ JWT token authentication
- ✅ Password hashing (bcrypt)
- ✅ SQL injection koruması (SQLAlchemy ORM)
- ✅ CORS yapılandırması
- ✅ Input validation (Pydantic)
- ✅ Environment variables (.env)
- ✅ CASCADE silme işlemleri (referential integrity)

## 📊 Database Şeması

### Users
- Temel bilgiler (username, email, password)
- Profil bilgileri (bio, location, profile_pic)
- Kimlik doğrulama (card_image, birthDate, gender)
- İstatistikler (followers_count, following_count)

### Posts
- İçerik (content, image, location)
- İlişkiler (author_id, hashtags)
- İstatistikler (likes_count, created_dt)

### Follow
- Takip ilişkileri (follower_id, following_id)

### Activity
- Beğeni aktiviteleri
- Takip aktiviteleri
- Zaman damgaları

### Hashtag
- Hashtag adı
- Post ilişkileri (many-to-many)

## 🚀 Development

### Backend Test
```bash
# FastAPI server başlat
uvicorn src.main:app --reload --port 8000

# API dokümantasyonunu aç
# http://127.0.0.1:8000/docs
```

### Frontend Test
```bash
cd frontend
npm run dev

# http://localhost:3000
```

### AI Model Test
```bash
# Content Moderator test
python src/ai/gorsel_test.py

# Card Reader test
python src/ai/card_test.py

# Text Moderator test
python src/ai/text_test.py
```

## 📝 Environment Variables

`.env` dosyasında şu değişkenler olmalı:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# JWT Secret
SECRET_KEY=your-super-secret-key-here

# Optional: SQLite for local testing
# DATABASE_URL=sqlite:///./veritabani.db
```

## 🎯 Kullanım Senaryoları

### 1. Kimlik Kartı ile Kayıt
1. Kimlik kartı fotoğrafı yükle
2. AI otomatik bilgileri çıkarır (OCR + Yüz tanıma)
3. Bilgileri kontrol et ve düzenle
4. Şifre belirle ve kayıt ol

### 2. Kart ile Giriş
1. Kimlik kartı fotoğrafı yükle
2. AI kartı veritabanındaki kartlarla eşleştirir
3. Eşleşme bulunursa otomatik giriş

### 3. Güvenli Gönderi Paylaşımı
1. Görsel ve/veya metin hazırla
2. AI otomatik moderasyon yapar:
   - Görsel içerik analizi (CLIP)
   - Görseldeki yazı kontrolü (OCR)
   - Metin içerik analizi
3. Uygunsa paylaşılır, değilse detaylı hata mesajı

## 📄 Lisans

Bu proje eğitim amaçlı geliştirilmiştir.

