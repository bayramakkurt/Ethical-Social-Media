#Main APP

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine #Kendi yazdığımız database dosyasından Base ve engine değişkenlerini aldık.
from .api import router

Base.metadata.create_all(bind = engine)



app = FastAPI(
    title="Social Media APP",
    description="Protect Social Media APP",
    version="0.1"
)

# CORS Middleware - Frontend ile backend arasındaki iletişim için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URL'leri
    allow_credentials=True,
    allow_methods=["*"],  # Tüm HTTP metodları
    allow_headers=["*"],  # Tüm headerlar
)

app.include_router(router)