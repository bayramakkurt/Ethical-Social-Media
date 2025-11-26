#Business Logic = Service Katmanı

import os
from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.orm import Session

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime

from .models import User
from .schemas import UserCreate, UserUpdate

# .env dosyasından environment variables'ları yükle
load_dotenv()

bcrypt_context = CryptContext(schemes= ["bcrypt"], deprecated = "auto") #Şifreleri hashlemek için bağlam olarak bcrypt kullanıldı.
oauth2_bearer = OAuth2PasswordBearer(tokenUrl= "v1/auth/token") #Kullanıcı Bearer token almak için endpointe gitmeli ve giriş yapmalı
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")  # .env'den al, yoksa fallback
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINS = 60 * 24 * 30 #Token expire süresi 30 gün olacak.


#Mevcut Kullanıcıları Kontrol
async def existing_user(db: Session, username: str = None, email: str = None):
    """Kullanıcı adı veya email ile kullanıcı ara"""
    if username:
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            return db_user
    
    if email:
        db_user = db.query(User).filter(User.email == email).first()
        if db_user:
            return db_user
    
    return None

#Token Oluşturma
async def create_access_token(username: str, id: int):
    expires = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINS)
    encode = {"sub": username, "id": id, "exp": expires}
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

#Tokenden Kullanıcıyı Alma
async def get_current_user(db: Session, token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get("sub")
        id: str = payload.get("id")
        expires: datetime = payload.get("exp")
        if datetime.fromtimestamp(expires) < datetime.now():
            return None
        if username is None or id is None:
            return None
        return db.query(User).filter(User.id == id).first()
    except JWTError:
        return None
    
#Kullanıcı Bilgilerini Getirme
async def get_user_from_user_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

#Kullanıcı Oluşturma
async def create_user(db: Session, user: UserCreate):
    db_user = User(
        email = user.email.lower().strip(),
        username = user.username.lower().strip(),
        hashed_password = bcrypt_context.hash(user.password),
        birthDate = user.birthDate or None,
        gender = user.gender or None,
        biography = user.biography or None,
        location = user.location or None,
        profile_pic = user.profile_pic or None,
        card_image = user.card_image or None,
        name = user.name or None
    )
    db.add(db_user)
    db.commit()

    return db_user

#Authentication
async def authenticate(db: Session, username: str, password: str):
    """Kullanıcı adı veya email ile giriş"""
    # Önce username olarak kontrol et
    db_user = db.query(User).filter(User.username == username).first()
    
    # Bulunamadıysa email olarak kontrol et
    if not db_user:
        db_user = db.query(User).filter(User.email == username).first()
    
    # Hala bulunamadıysa None dön
    if not db_user:
        return None
    
    # Şifreyi kontrol et
    if not bcrypt_context.verify(password, db_user.hashed_password):
        return None
    
    return db_user

#Update User
async def update_user(db:Session, db_user: User, user_update: UserUpdate):
    db_user.biography = user_update.biography or db_user.biography
    db_user.birthDate = user_update.birthDate or db_user.birthDate
    db_user.name = user_update.name or db_user.name
    db_user.gender = user_update.gender or db_user.gender
    db_user.location = user_update.location or db_user.location
    db_user.profile_pic = user_update.profile_pic or db_user.profile_pic
    db_user.card_image = user_update.card_image or db_user.card_image

    db.commit()

#Delete User
async def delete_user(db: Session, user_id: int):
    """
    Kullanıcıyı ve tüm ilişkili verilerini siler.
    Sırayla temizlenir:
    - Activity kayıtları
    - Follow ilişkileri (takipçi ve takip edilenler)
    - Post hashtags (many-to-many)
    - Post likes (many-to-many)
    - Posts
    - User
    """
    from ..activity.models import Activity
    from .models import Follow
    from ..post.models import Post, post_likes, post_hashtags
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    
    # Kullanıcının post ID'lerini al
    user_post_ids = [post.id for post in db.query(Post.id).filter(Post.author_id == user_id).all()]
    
    # 1. Activity kayıtlarını temizle
    db.query(Activity).filter(
        (Activity.username == db_user.username) | 
        (Activity.username_like == db_user.username) |
        (Activity.followed_username == db_user.username)
    ).delete(synchronize_session=False)
    
    # 2. Follow kayıtlarını temizle (hem takipçi hem takip edilen)
    db.query(Follow).filter(
        (Follow.follower_id == user_id) |
        (Follow.following_id == user_id)
    ).delete(synchronize_session=False)
    
    # 3. Post hashtags ilişkilerini temizle (kullanıcının postları için)
    if user_post_ids:
        db.execute(
            post_hashtags.delete().where(post_hashtags.c.post_id.in_(user_post_ids))
        )
    
    # 4. Post likes kayıtlarını temizle
    if user_post_ids:
        db.execute(
            post_likes.delete().where(post_likes.c.post_id.in_(user_post_ids))
        )
    
    # 5. Kullanıcının beğendiği postlardan çıkar
    db.execute(
        post_likes.delete().where(post_likes.c.user_id == user_id)
    )
    
    # 6. Kullanıcının postlarını sil
    if user_post_ids:
        db.query(Post).filter(Post.author_id == user_id).delete(synchronize_session=False)
    
    # 7. Kullanıcıyı sil
    db.delete(db_user)
    db.commit()
    
    return True