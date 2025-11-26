from sqlalchemy.orm import Session

from ..auth.models import Follow, User
from ..activity.models import Activity
from .schemas import FollowersList, FollowingList, Profile
from ..auth.service import get_user_from_user_id, existing_user

#Follow
async def follow_service(db: Session, follower: str, following: str):
    db_follower = await existing_user(db, follower, "")
    db_following = await existing_user(db, following, "")
    if not db_follower or not db_following:
        return False
    
    db_follow = db.query(Follow).filter_by(follower_id = db_follower.id, following_id = db_following.id).first()
    if db_follow:
        return False
    
    db_follow = Follow(follower_id = db_follower.id, following_id = db_following.id)

    db.add(db_follow)

    db_follower.following_count += 1
    db_following.followers_count += 1

    follow_activity = Activity(username = following, followed_username = db_follower.username, followed_user_picture = db_follower.profile_pic)
    db.add(follow_activity)

    db.commit()

#Unfollow
async def unfollow_service(db: Session, follower: str, following: str):
    db_follower = await existing_user(db, follower, "")
    db_following = await existing_user(db, following, "")
    if not db_follower or not db_following:
        return False
    
    db_follow = db.query(Follow).filter_by(follower_id = db_follower.id, following_id = db_following.id).first()
    if not db_follow:
        return False
    
    # Follow kaydını sil
    db.delete(db_follow)

    # Sayaçları güncelle
    db_follower.following_count -= 1
    db_following.followers_count -= 1
    
    # Activity kaydını sil
    db.query(Activity).filter(
        Activity.username == following,
        Activity.followed_username == follower
    ).delete(synchronize_session=False)

    db.commit()

#Get Followers
async def get_followers_service(db: Session, user_id: int):
    db_user = await get_user_from_user_id(db, user_id)
    if not db_user:
        return []
    
    db_followers = db.query(Follow).filter_by(following_id = user_id).join(User, User.id == Follow.follower_id).all()
    followers = []
    for user in db_followers:
        followers.append({
            "profile_pic": user.follower.profile_pic,
            "name": user.follower.name,
            "username": user.follower.username
        })
    
    return FollowersList(followers=followers)

#Get Following
async def get_following_service(db: Session, user_id: int):
    db_user = await get_user_from_user_id(db, user_id)
    if not db_user:
        return []
    
    db_following = db.query(Follow).filter_by(follower_id = user_id).join(User, User.id == Follow.following_id).all()
    following = []
    for user in db_following:
        following.append({
            "profile_pic": user.follower.profile_pic,
            "name": user.follower.name,
            "username": user.follower.username
        })
    
    return FollowingList(following=following)

#Check Follow
async def check_follow_service(db: Session, current_user: str, user: str):
    db_follower = await existing_user(db, current_user, "")
    db_following = await existing_user(db, user, "")
    if not  db_follower or not db_following:
        return False

    db_following = db.query(Follow).filter_by(follower_id = db_follower.id, following_id = db_following.id).first()
    if db_following:
        return True
    return False
