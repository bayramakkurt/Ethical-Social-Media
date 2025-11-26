#Veritabanı modellerine dayalı modellerdir. BaseModel burada oluşturulur. Her veritabanı modeli için bir schema oluşturmamız lazım

from pydantic import BaseModel
from datetime import date,datetime
from typing import Optional
from .enums import Gender

class UserBase(BaseModel): #Temel User modeli oluşturuldu. Parametreler zorunlu ve opsiyonel olarak atandı.
    email: str
    username: str
    name: str
    birthDate: Optional[date] = None
    gender: Optional[Gender] = None
    biography: Optional[str] = None
    location: Optional[str] = None
    profile_pic: Optional[str] = None
    card_image: Optional[str] = None

class UserCreate(UserBase): #Kullanıcı kaydı için temel model harici istenen yeni bilgiler için ek model oluştu ve kalıtım aldı.
    password: str

class UserUpdate(BaseModel): #Kullanıcı bilgileri güncellenmek istenirse sadece aşağıdaki verileri değiştirebilecek ve hepsi opsiyonel.
    name: Optional[str] = None
    birthDate: Optional[date] = None
    gender: Optional[Gender] = None
    biography: Optional[str] = None
    location: Optional[str] = None
    profile_pic: Optional[str] = None
    card_image: Optional[str] = None

class User(UserBase):
    id: int
    created_dt: datetime

    class Config:
        orm_mode = True #sayesinde SQLAlchemy modelinden (DB’den) direkt User Pydantic modeline veri çekebiliriz.