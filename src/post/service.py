from sqlalchemy.orm import Session
from sqlalchemy import desc
import re

from .schemas import PostCreate, Post as PostSchema, Hashtag as HashtagService
from .models import Post, Hashtag, post_hashtags
from ..auth.models import User
from ..auth.schemas import User as UserSchema
from ..activity.models import Activity


#Create Hashtag from Posts Content
async def create_hashtag_service(db: Session, post: Post):
    regex = r"#\w+"
    matches = re.findall(regex, post.content)

    for match in matches:
        name = match[1:]

        hashtag = db.query(Hashtag).filter(Hashtag.name == name).first()
        if not hashtag:
            hashtag = Hashtag(name=name)
            db.add(hashtag)
            db.commit()
        post.hashtags.append(hashtag)


#Create Post
async def create_post_service(db: Session, post: PostCreate, user_id: int):
    db_post = Post(
        content = post.content,
        image = post.image,
        location = post.location,
        author_id = user_id
    )
    await create_hashtag_service(db, db_post)

    db.add(db_post)
    db.commit()
    return db_post

#Get User Posts
async def get_user_posts_service(db: Session, user_id: int, current_username: str = None) -> list[PostSchema]:
    posts = db.query(Post, User).join(User).filter(Post.author_id == user_id).order_by(desc(Post.created_dt)).all()
    
    result = []
    
    for post, user in posts:
        # Likes ve comments count hesapla
        from ..activity.models import Activity
        likes_count = db.query(Activity).filter(
            Activity.liked_post_id == post.id
        ).count()
        
        # Comments için şimdilik 0 (comment sistemi henüz yok)
        comments_count = 0
        
        # Current user bu postu beğenmiş mi?
        is_liked = False
        if current_username:
            is_liked = db.query(Activity).filter(
                Activity.liked_post_id == post.id,
                Activity.username_like == current_username
            ).first() is not None
        
        result.append({
            "id": post.id,
            "content": post.content,
            "image_url": post.image,
            "location": post.location,
            "created_at": post.created_dt.isoformat() if post.created_dt else None,
            "author_id": post.author_id,
            "likes_count": likes_count,
            "comments_count": comments_count,
            "is_liked": is_liked,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.name,
                "profile_pic": user.profile_pic
            }
        })
    
    return result

#Get Posts from Hashtag
async def get_posts_from_hashtag_service(db: Session, hashtag_name: str):
    hashtag = db.query(Hashtag).filter_by(name= hashtag_name).first()
    if not hashtag:
        return None
    return hashtag.posts

#Get Random Posts (return latest posts of all users)
async def get_random_posts_service(db: Session, page: int=1, limit: int=10, hashtag: str = None, current_username: str = None):
    total_posts = db.query(Post).count()

    offset = (page - 1) * limit
    if offset >= total_posts:
        return []
    
    posts = db.query(Post, User).join(User).order_by(desc(Post.created_dt))

    if hashtag:
        # Hashtag başındaki # işaretini kaldır
        hashtag_name = hashtag.lstrip('#')
        posts = posts.join(post_hashtags).join(Hashtag).filter(Hashtag.name == hashtag_name)

    posts = posts.offset(offset).limit(limit).all()

    result = []
    
    for post, user in posts:
        # Likes ve comments count hesapla
        from ..activity.models import Activity
        likes_count = db.query(Activity).filter(
            Activity.liked_post_id == post.id
        ).count()
        
        # Comments için şimdilik 0 (comment sistemi henüz yok)
        comments_count = 0
        
        # Current user bu postu beğenmiş mi?
        is_liked = False
        if current_username:
            is_liked = db.query(Activity).filter(
                Activity.liked_post_id == post.id,
                Activity.username_like == current_username
            ).first() is not None
        
        result.append({
            "id": post.id,
            "content": post.content,
            "image_url": post.image,
            "location": post.location,
            "created_at": post.created_dt.isoformat() if post.created_dt else None,
            "author_id": post.author_id,
            "likes_count": likes_count,
            "comments_count": comments_count,
            "is_liked": is_liked,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.name,
                "profile_pic": user.profile_pic
            }
        })
    
    return result


#Get Post by Post ID
async def get_post_from_post_id_service(db: Session, post_id: int) -> PostSchema:
    return db.query(Post).filter(Post.id == post_id).first()

#Delete Post
async def delete_post_service(db: Session, post_id: int):
    """
    Postu ve ilişkili tüm verileri siler.
    CASCADE sayesinde otomatik olarak silinir:
    - post_hashtags ilişkileri
    - post_likes ilişkileri
    - Activity kayıtları manuel temizlenir
    """
    post = await get_post_from_post_id_service(db, post_id)
    if not post:
        return False
    
    # Activity kayıtlarını temizle (bu post ile ilgili beğenileri)
    db.query(Activity).filter(Activity.liked_post_id == post_id).delete(synchronize_session=False)
    
    # Postu sil (CASCADE ile post_hashtags ve post_likes otomatik silinir)
    db.delete(post)
    db.commit()
    return True


#Like Post
async def like_post_service(db: Session, post_id: int, username: str):
    #Post varmı yokmu kontrol et
    post = await get_post_from_post_id_service(db, post_id)
    if not post:
        return False, "Geçersiz Post ID."
    #Kullanıcı varmı yokmu kontrol et
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False, "Geçersiz Kullanıcı Adı."
    #Kullanıcı zaten postu beğenmişmi kontrol et
    if user in post.liked_by_users:
        return False, "Kullanıcı bu gönderiyi zaten beğendi."
    #Kullanıcı için postu beğen listeye ekle ve sayacı arttır
    post.liked_by_users.append(user)
    post.likes_count = len(post.liked_by_users)

    #Aktivite olarak ekle
    like_activity = Activity(username= post.author.username, liked_post_id = post_id, username_like = username, liked_post_image = post.image)
    db.add(like_activity)

    db.commit()
    return True, "Başarılı"

#Unlike Post
async def unlike_post_service(db: Session, post_id: int, username: str):
    #Post varmı yokmu kontrol et
    post = await get_post_from_post_id_service(db, post_id)
    if not post:
        return False, "Geçersiz Post ID."
    #Kullanıcı varmı yokmu kontrol et
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False, "Geçersiz Kullanıcı Adı."
    #Kullanıcı zaten postu beğenmişmi kontrol et
    if not user in post.liked_by_users:
        return False, "Kullanıcı bu gönderiyi zaten beğenmedi."
    
    # Beğeni listesinden çıkar
    post.liked_by_users.remove(user)
    post.likes_count = len(post.liked_by_users)
    
    # Activity kaydını sil
    db.query(Activity).filter(
        Activity.liked_post_id == post_id,
        Activity.username_like == username
    ).delete(synchronize_session=False)

    db.commit()
    return True, "Başarılı"

#Users Who Liked Post
async def liked_users_post_service(db: Session, post_id: int) -> list[UserSchema]:
    post = await get_post_from_post_id_service(db, post_id)
    if not post:
        return []
    
    liked_users = post.liked_by_users
    return liked_users