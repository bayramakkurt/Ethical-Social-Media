from fastapi import APIRouter, Depends, status, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional
import base64
import io
from PIL import Image

from ..database import get_db
from .schemas import PostCreate, Post
from .service import create_post_service, delete_post_service, create_hashtag_service, get_post_from_post_id_service, get_posts_from_hashtag_service, get_random_posts_service, get_user_posts_service, like_post_service, unlike_post_service,liked_users_post_service
from ..auth.service import get_current_user, existing_user
from ..auth.schemas import User
from ..ai.content_moderator import ContentModerator
from ..ai.text_moderator import TextModerator
import easyocr


router = APIRouter(prefix="/posts", tags=["posts"])

#Create Post (Dosya yükleme veya sadece metin)
@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(
    content: str = Form(...),
    image_file: Optional[UploadFile] = File(None),
    token: str = Form(...),
    location: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Post oluşturma endpoint'i.
    - Görsel yükleme opsiyonel (image_file)
    - Sadece metin paylaşımı yapılabilir
    - Görsel varsa: NSFW, kan, şiddet + OCR küfür kontrolü
    - Metin her zaman küfür kontrolünden geçer
    """
    # Token kontrol
    user = await get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmadan bu işlemi gerçekleştiremezsiniz."
        )
    
    image_data_uri = None
    
    # Görsel yüklendiyse işle
    if image_file:
        try:
            # Dosyayı oku
            contents = await image_file.read()
            image = Image.open(io.BytesIO(contents))
            
            # RGB'ye çevir
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 1. Görsel İçerik Moderasyonu (NSFW, Kan, Şiddet)
            content_mod = ContentModerator()
            content_result = content_mod.analyze_image(image)
            
            # Numpy array'i listeye çevir
            if 'all_scores' in content_result:
                content_result['all_scores'] = content_result['all_scores'].tolist()
            
            # Eğer görsel paylaşılabilir değilse reddet
            if not content_result.get("is_shareable", True):
                # Detaylı ve Türkçe hata mesajı oluştur
                category_tr = content_result.get("category_tr", "Uygunsuz İçerik")
                confidence = content_result.get("score", 0)
                detected_label = content_result.get("label", "")
                
                error_message = f"🚫 Görsel İçerik Politikası İhlali\n\n"
                error_message += f"Tespit Edilen Kategori: {category_tr}\n"
                error_message += f"Güven Oranı: %{confidence:.1f}\n\n"
                
                # Kategoriye özel detaylı açıklama
                category = content_result.get("category", "")
                if category == "violence":
                    error_message += "⚠️ Bu görsel içerir:\n"
                    error_message += "• Fiziksel şiddet veya kavga sahnesi\n"
                    error_message += "• Kan, yara veya vahşet\n"
                    error_message += "• Ceset veya ağır kaza görüntüsü\n"
                    error_message += "• İşkence veya acı çektiren içerik\n\n"
                    error_message += "Lütfen şiddet içermeyen bir görsel yükleyin."
                    
                elif category == "nsfw":
                    error_message += "⚠️ Bu görsel içerir:\n"
                    error_message += "• Açık saçık cinsel içerik\n"
                    error_message += "• Çıplaklık veya cinsel organlar\n"
                    error_message += "• Erotik veya müstehcen pozlar\n"
                    error_message += "• Pornografik materyal\n\n"
                    error_message += "Lütfen uygun bir görsel yükleyin."
                    
                elif category == "weapon":
                    error_message += "⚠️ Bu görsel içerir:\n"
                    error_message += "• Ateşli silah (tabanca, tüfek vb.)\n"
                    error_message += "• Tehditkar şekilde tutulan kesici aletler\n"
                    error_message += "• Yasadışı uyuşturucu madde\n"
                    error_message += "• Terör veya savaş görüntüsü\n\n"
                    error_message += "Lütfen silah veya tehdit içermeyen bir görsel yükleyin."
                    
                elif category == "hate":
                    error_message += "⚠️ Bu görsel içerir:\n"
                    error_message += "• Hakaret edici el işaretleri\n"
                    error_message += "• Nefret söylemi sembolleri\n"
                    error_message += "• Irkçı veya ayrımcı içerik\n\n"
                    error_message += "Lütfen saygılı bir görsel yükleyin."
                else:
                    error_message += "Lütfen topluluk kurallarına uygun bir görsel yükleyin."
                
                clean_result = {k: v for k, v in content_result.items() if k != 'all_scores'}
                raise HTTPException(
                    status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                    detail={
                        "message": error_message,
                        "category": category_tr,
                        "confidence": confidence,
                        "detected_label": detected_label,
                        "moderation_details": clean_result
                    }
                )
            
            # 2. Görseldeki Metin Moderasyonu (OCR + Küfür Kontrolü)
            try:
                import torch
                reader = easyocr.Reader(['tr', 'en'], gpu=torch.cuda.is_available())
                ocr_results = reader.readtext(image, detail=0)
                
                if ocr_results:
                    extracted_text = " ".join(ocr_results)
                    
                    text_mod = TextModerator()
                    text_result = text_mod.analyze_text(extracted_text)
                    
                    if text_result.get("is_toxic", False):
                        confidence = text_result.get("score", 0) * 100
                        
                        # Metni kısalt (max 150 karakter)
                        display_text = extracted_text[:150] + "..." if len(extracted_text) > 150 else extracted_text
                        
                        error_message = f"🚫 Görseldeki Metin Moderasyon İhlali\n\n"
                        error_message += f"Tespit Edilen Metin:\n\"{display_text}\"\n\n"
                        error_message += f"Güven Oranı: %{confidence:.1f}\n\n"
                        error_message += "⚠️ Bu görseldeki yazı içerir:\n"
                        error_message += "• Küfür veya hakaret\n"
                        error_message += "• Saldırgan dil\n"
                        error_message += "• Uygunsuz ifadeler\n\n"
                        error_message += "Lütfen görselde uygunsuz metin bulundurmayın."
                        
                        raise HTTPException(
                            status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                            detail={
                                "message": error_message,
                                "extracted_text": extracted_text,
                                "confidence": confidence,
                                "moderation_details": text_result
                            }
                        )
            except HTTPException:
                raise
            except Exception as e:
                print(f"OCR moderasyon uyarısı: {str(e)}")
            
            # Base64'e çevir
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            image_data_uri = f"data:image/jpeg;base64,{image_base64}"
        
        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e)
            
            # Hata tipine göre kullanıcı dostu mesaj
            if "cannot identify image file" in error_msg.lower():
                user_message = "❌ Görsel Format Hatası\n\nYüklediğiniz dosya geçerli bir görsel değil.\n\nDesteklenen formatlar: JPG, PNG, GIF, WebP"
            elif "image file is truncated" in error_msg.lower():
                user_message = "❌ Bozuk Görsel Dosyası\n\nGörsel dosyası hasarlı veya eksik.\n\nLütfen başka bir görsel deneyin."
            elif "out of memory" in error_msg.lower() or "cuda" in error_msg.lower():
                user_message = "❌ Görsel Çok Büyük\n\nGörsel boyutu çok büyük.\n\nLütfen daha küçük bir görsel yükleyin (Max: 10MB)"
            else:
                user_message = f"❌ Görsel İşleme Hatası\n\nGörsel işlenirken bir sorun oluştu.\n\nHata detayı: {error_msg[:100]}"
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=user_message
            )
    
    # 3. Post Metni Moderasyonu (Her zaman yapılır)
    if content:
        try:
            text_mod = TextModerator()
            text_result = text_mod.analyze_text(content)
            
            if text_result.get("is_toxic", False):
                confidence = text_result.get("score", 0) * 100
                
                # Metni kısalt preview için (max 100 karakter)
                display_content = content[:100] + "..." if len(content) > 100 else content
                
                error_message = f"🚫 Metin İçerik Politikası İhlali\n\n"
                error_message += f"Tespit Edilen Metin:\n\"{display_content}\"\n\n"
                error_message += f"Güven Oranı: %{confidence:.1f}\n\n"
                error_message += "⚠️ Bu metin içerir:\n"
                error_message += "• Küfür veya hakaret\n"
                error_message += "• Saldırgan dil\n"
                error_message += "• Uygunsuz ifadeler\n"
                error_message += "• Nefret söylemi\n\n"
                error_message += "Lütfen paylaşımınızda saygılı bir dil kullanın."
                
                raise HTTPException(
                    status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                    detail={
                        "message": error_message,
                        "confidence": confidence,
                        "moderation_details": text_result
                    }
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Metin moderasyon uyarısı: {str(e)}")
    
    # PostCreate objesi oluştur
    post_data = PostCreate(
        content=content,
        image=image_data_uri,  # None olabilir
        location=location
    )
    
    # Post oluştur
    db_post = await create_post_service(db, post_data, user.id)
    
    return db_post

#Get Current User Posts
@router.get("/user")
async def get_current_user_posts(token: str, db: Session = Depends(get_db)):
    #Token kontrol
    user = await get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmadan bu işlemi gerçekleştiremezsiniz."
        )
    return await get_user_posts_service(db, user.id, user.username)

#Get User Posts
@router.get("/user/{username}")
async def get_user_posts(username: str, token: str = None, db: Session = Depends(get_db)):
    #Kullanıcıyı bul
    user = await existing_user(db, username, "")
    
    # Current user kim?
    current_username = None
    if token:
        current_user = await get_current_user(db, token)
        if current_user:
            current_username = current_user.username

    return await get_user_posts_service(db, user.id, current_username)

#Get Posts from Hashtag
@router.get("/hashtag/{hashtag}")
async def get_posts_from_hashtag(hashtag: str, db: Session = Depends(get_db)):
    return await get_posts_from_hashtag_service(db, hashtag)

#Get Random Posts
@router.get("/feed")
async def get_random_posts(token: str = None, page: int=1, limit: int=5, hashtag: str = None, db: Session = Depends(get_db)):
    # Current user kim?
    current_username = None
    if token:
        current_user = await get_current_user(db, token)
        if current_user:
            current_username = current_user.username
    
    return await get_random_posts_service(db, page, limit, hashtag, current_username)

#Delete Post
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(token: str, post_id: int, db: Session = Depends(get_db)):
    #Token kontrol
    user = await get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmadan bu işlemi gerçekleştiremezsiniz."
        )
    post = await get_post_from_post_id_service(db, post_id)
    if post.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bu gönderiyi silmek için yetkiniz yok."
        )
    await delete_post_service(db, post_id)

#Like Post
@router.post("/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_post(post_id: int, token: str, db: Session = Depends(get_db)):
    # Token kontrol
    user = await get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmadan bu işlemi gerçekleştiremezsiniz."
        )
    
    response, detail = await like_post_service(db, post_id, user.username)
    if response == False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

#Unlike Post
@router.post("/unlike", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(post_id: int, token: str, db: Session = Depends(get_db)):
    # Token kontrol
    user = await get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmadan bu işlemi gerçekleştiremezsiniz."
        )
    
    response, detail = await unlike_post_service(db, post_id, user.username)
    if response == False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )
    
#Users Like Post
@router.get("/likes/{post_id}", response_model=list[User])
async def users_like_post(post_id: int, db: Session = Depends(get_db)):
    return await liked_users_post_service(db, post_id)


#Get Post
@router.get("{post_id}", response_model=Post)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    db_post = await get_post_from_post_id_service(db, post_id)
    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geçersiz Post ID."
        )
    return db_post
