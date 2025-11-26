#API tanımlandığı kısımdır = Controller

#SignUp - Login - Generate Token - Get Current User - Update User

from fastapi import APIRouter, Depends, status, HTTPException, File, UploadFile, Form
from fastapi.security import OAuth2PasswordRequestForm 
from sqlalchemy.orm import Session
from datetime import datetime, date
import base64
import io
from PIL import Image
from typing import Optional

from .schemas import UserCreate, UserUpdate, User as UserSchema
from .enums import Gender
from ..database import get_db
from .service import existing_user, create_access_token, get_current_user, create_user as create_user_service, authenticate, update_user as update_user_service, delete_user as delete_user_service
from ..ai.card_reader import SpatialCardReader
from ..ai.card_matcher import CardMatcher

router = APIRouter(prefix="/auth", tags=["auth"])

#CARD READER ENDPOINT (Kart okuma - sadece veri çıkarma)
@router.post("/read-card", status_code=status.HTTP_200_OK)
async def read_card(card_image: UploadFile = File(...)):
    """
    Kart görselini okur ve çıkarılan verileri döner.
    Kullanıcı bu verileri görecek, düzenleyecek ve sonra signup yapacak.
    """
    try:
        # Dosyayı oku
        contents = await card_image.read()
        image = Image.open(io.BytesIO(contents))
        
        # Görseli RGB'ye çevir
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Kart okuyucu başlat ve analiz et
        reader = SpatialCardReader()
        card_data = reader.analyze_card(image)
        
        if card_data.get("error"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kart okuma hatası: {card_data['error']}"
            )
        
        parsed = card_data.get("parsed_data", {})
        
        # Profil fotoğrafını base64'e çevir
        profile_pic_base64 = None
        if card_data.get("face_found") and card_data.get("face_image"):
            buffered = io.BytesIO()
            card_data["face_image"].save(buffered, format="JPEG")
            face_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            profile_pic_base64 = f"data:image/jpeg;base64,{face_base64}"
        
        # Orijinal kart görselini base64'e çevir
        card_image_base64 = None
        buffered_card = io.BytesIO()
        image.save(buffered_card, format="JPEG")
        card_base64 = base64.b64encode(buffered_card.getvalue()).decode('utf-8')
        card_image_base64 = f"data:image/jpeg;base64,{card_base64}"
        
        # Doğum tarihini ISO 8601 formatına çevir (YYYY-MM-DD)
        birth_date_iso = ""
        if parsed.get("Dogum_Tarihi"):
            try:
                from datetime import datetime as dt
                date_str = parsed["Dogum_Tarihi"].strip()
                # Farklı formatları dene
                for fmt in ["%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                    try:
                        parsed_date = dt.strptime(date_str, fmt)
                        birth_date_iso = parsed_date.strftime("%Y-%m-%d")
                        break
                    except:
                        continue
            except:
                pass
        
        # Cinsiyeti male/female/other formatına çevir
        gender_formatted = None
        if parsed.get("Cinsiyet"):
            gender_map = {"E": "male", "K": "female", "ERKEK": "male", "KADIN": "female", "M": "male", "F": "female"}
            gender_text = parsed["Cinsiyet"].upper()
            gender_formatted = gender_map.get(gender_text, "other")
        
        # Frontend'e gönderilecek temiz veri
        return {
            "success": True,
            "card_data": {
                "name": parsed.get("Isim_Soyisim", ""),
                "email": parsed.get("Email", ""),
                "company": parsed.get("Sirket", ""),
                "title": parsed.get("Unvan", ""),
                "id_number": parsed.get("ID_Sicil", ""),
                "location": parsed.get("Konum", ""),
                "birthDate": birth_date_iso,  # Format: YYYY-MM-DD (ISO 8601)
                "gender": gender_formatted,  # male veya female
                "profile_pic": profile_pic_base64,
                "card_image": card_image_base64,  # Orijinal kart görseli
                "face_found": card_data.get("face_found", False)
            },
            "message": "Kart başarıyla okundu. Lütfen bilgileri kontrol edip düzenleyin."
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kart işleme hatası: {str(e)}"
        )

#SIGNUP
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    #Mevcut kullanıcıyı kontrol etme
    db_user = await existing_user(db, user.username, user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kullanıcı adı veya e-mail zaten kullanımda."
        )
    
    # Kullanıcı oluştur
    db_user = await create_user_service(db, user)
    access_token = await create_access_token(user.username, db_user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username
    }

#LOGIN AND GENERATE TOKEN
@router.post("/login" , status_code=status.HTTP_201_CREATED)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = await authenticate(db, form_data.username, form_data.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz Kullanıcı Adı veya Parola."
        )
    access_token = await create_access_token(db_user.username, db_user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

#LOGIN WITH CARD (Kart eşleştirme ile giriş)
@router.post("/login-with-card", status_code=status.HTTP_200_OK)
async def login_with_card(card_image: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Kart görseli yükleyerek giriş yapma.
    Yüklenen kart, veritabanındaki tüm kullanıcıların kartlarıyla eşleştirilir.
    Eşleşme bulunursa token döner.
    """
    try:
        # Dosyayı oku
        contents = await card_image.read()
        uploaded_image = Image.open(io.BytesIO(contents))
        
        # Görseli RGB'ye çevir
        if uploaded_image.mode != 'RGB':
            uploaded_image = uploaded_image.convert('RGB')
        
        # Yüklenen kartı base64'e çevir
        buffered = io.BytesIO()
        uploaded_image.save(buffered, format="JPEG")
        uploaded_card_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # CardMatcher başlat
        matcher = CardMatcher(algorithm="orb")  # ORB daha hızlı
        
        # Veritabanındaki tüm kullanıcıları al (card_image olan)
        from .models import User
        users_with_cards = db.query(User).filter(User.card_image.isnot(None)).all()
        
        if not users_with_cards:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sistemde kayıtlı kartlı kullanıcı bulunamadı."
            )
        
        # Her kullanıcının kartıyla eşleştir
        best_match = None
        best_confidence = 0
        best_match_details = None
        
        for user in users_with_cards:
            result = matcher.match_cards(uploaded_card_base64, user.card_image)
            
            if result.get("is_match") and result.get("confidence", 0) > best_confidence:
                best_match = user
                best_confidence = result.get("confidence", 0)
                best_match_details = result
        
        # Eşleşme bulunamadıysa veya güven skoru düşükse
        MINIMUM_CONFIDENCE = 60  # %60 minimum güven skoru
        
        if not best_match or best_confidence < MINIMUM_CONFIDENCE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "Kart eşleşmesi bulunamadı veya güven skoru yetersiz.",
                    "best_confidence": best_confidence if best_match else 0,
                    "minimum_required": MINIMUM_CONFIDENCE,
                    "suggestion": "Lütfen kartı daha net çekin veya kullanıcı adı ve şifre ile giriş yapın."
                }
            )
        
        # Token oluştur ve dön
        access_token = await create_access_token(best_match.username, best_match.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": best_match.username,
            "match_confidence": best_confidence,
            "message": "Kart eşleşmesi başarılı! Hoşgeldiniz."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kart eşleştirme hatası: {str(e)}"
        )

#GET CURRENT USER
@router.get("/profile", status_code=status.HTTP_200_OK, response_model=UserSchema)
async def current_user(token: str, db: Session = Depends(get_db)):
    db_user =  await get_current_user(db, token)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz Token."
        )
    return db_user

#UPDATE USER
@router.put("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def update_user(
    username: str, 
    token: str = Form(...),
    name: Optional[str] = Form(None),
    birthDate: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    biography: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    profile_pic_file: Optional[UploadFile] = File(None),
    card_image_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Kullanıcı bilgilerini güncelleme endpoint'i.
    - profile_pic_file: Profil fotoğrafı (dosya - opsiyonel)
    - card_image_file: Kart görseli (dosya - opsiyonel)
    - Diğer alanlar form data olarak gönderilir
    """
    db_user = await get_current_user(db, token)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı veya token geçersiz."
        )

    if db_user.username != username.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kullanıcıyı güncellemeye yetkili değilsiniz."
        )
    
    # UserUpdate objesi oluştur
    user_update_data = UserUpdate(
        name=name,
        birthDate=None,
        gender=None,
        biography=biography,
        location=location,
        profile_pic=None,
        card_image=None
    )
    
    # Doğum tarihi parse
    if birthDate:
        try:
            from datetime import datetime as dt
            user_update_data.birthDate = dt.strptime(birthDate, "%Y-%m-%d").date()
        except:
            pass
    
    # Cinsiyet parse
    if gender and gender in ["male", "female", "other"]:
        user_update_data.gender = Gender(gender)
    
    # Profil fotoğrafı yüklendiyse işle
    if profile_pic_file:
        try:
            contents = await profile_pic_file.read()
            image = Image.open(io.BytesIO(contents))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            profile_pic_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            user_update_data.profile_pic = f"data:image/jpeg;base64,{profile_pic_base64}"
        except Exception as e:
            print(f"Profil fotoğrafı yükleme hatası: {str(e)}")
    
    # Kart görseli yüklendiyse işle
    if card_image_file:
        try:
            contents = await card_image_file.read()
            image = Image.open(io.BytesIO(contents))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            card_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            user_update_data.card_image = f"data:image/jpeg;base64,{card_image_base64}"
        except Exception as e:
            print(f"Kart görseli yükleme hatası: {str(e)}")
    
    await update_user_service(db, db_user, user_update_data)
    
    # Güncellenmiş kullanıcıyı döndür
    return {
        "success": True,
        "message": "Profil başarıyla güncellendi"
    }    

#DELETE USER
@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(username: str, token: str, db: Session = Depends(get_db)):
    """
    Kullanıcıyı ve tüm ilişkili verilerini siler.
    Otomatik olarak silinir:
    - Tüm postları
    - Tüm beğenileri
    - Tüm takipçi/takip edilenler
    - Tüm aktivite kayıtları
    """
    # Token kontrol
    current_user = await get_current_user(db, token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token."
        )
    
    # Sadece kendi hesabını silebilir
    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece kendi hesabınızı silebilirsiniz."
        )
    
    # Kullanıcıyı sil
    success = await delete_user_service(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı."
        )



