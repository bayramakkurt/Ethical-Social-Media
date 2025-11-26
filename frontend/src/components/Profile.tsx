import { useState, useEffect } from 'react';
import { profileAPI, postAPI, authAPI, getCurrentUser } from '../lib/api';

interface ProfileProps {
  username: string;
}

export default function Profile({ username }: ProfileProps) {
  const [profile, setProfile] = useState<any>(null);
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  
  useEffect(() => {
    loadProfile();
    setCurrentUser(getCurrentUser());
  }, [username]);
  
  const loadProfile = async () => {
    try {
      const [profileData, postsData] = await Promise.all([
        profileAPI.getProfile(username),
        postAPI.getUserPostsByUsername(username, 1, 50)
      ]);
      setProfile(profileData);
      setPosts(postsData);
    } catch (error) {
      console.error('Profil yüklenemedi:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleFollow = async () => {
    try {
      if (profile.is_following) {
        await profileAPI.unfollow(username);
      } else {
        await profileAPI.follow(username);
      }
      await loadProfile();
    } catch (error) {
      console.error('Takip hatası:', error);
    }
  };

  const handleLike = async (postId: number, isLiked: boolean) => {
    try {
      if (isLiked) {
        await postAPI.unlikePost(postId);
      } else {
        await postAPI.likePost(postId);
      }
      await loadProfile();
    } catch (error) {
      console.error('Beğeni hatası:', error);
    }
  };
  
  const isOwner = currentUser?.username === username;
  
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: 'linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%)'
      }}>
        <div className="loading" style={{ width: '60px', height: '60px' }}></div>
      </div>
    );
  }
  
  if (!profile) {
    return (
      <div style={{ 
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}>
        <div style={{
          background: '#2a2a2a',
          borderRadius: '24px',
          padding: '60px 40px',
          textAlign: 'center',
          maxWidth: '400px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <div style={{ fontSize: '80px', marginBottom: '20px' }}>😕</div>
          <h2 style={{ fontSize: '28px', fontWeight: '700', color: '#fff', marginBottom: '15px' }}>
            Kullanıcı Bulunamadı
          </h2>
          <p style={{ color: '#8a8a8a', marginBottom: '30px' }}>
            Aradığın profil mevcut değil
          </p>
          <a href="/feed" className="btn btn-primary" style={{ textDecoration: 'none' }}>
            Ana Sayfaya Dön
          </a>
        </div>
      </div>
    );
  }
  
  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%)'
    }}>
      {/* Top Bar */}
      <div style={{
        padding: '20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <a href="/feed" style={{ textDecoration: 'none', color: '#8a8a8a', fontSize: '24px' }}>←</a>
          <div style={{ 
            fontSize: '28px', 
            fontWeight: '800', 
            color: '#FE3C72',
            letterSpacing: '-1px'
          }}>
            Profil
          </div>
        </div>
        {isOwner && (
          <button 
            onClick={() => {
              authAPI.logout();
              window.location.href = '/login';
            }}
            style={{
              background: 'transparent',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '8px'
            }}
          >
            🚪
          </button>
        )}
      </div>

      {/* Profile Header */}
      <div style={{
        padding: '30px 20px',
        maxWidth: '600px',
        margin: '0 auto'
      }}>
        <div style={{
          background: '#2a2a2a',
          borderRadius: '24px',
          padding: '40px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          marginBottom: '30px'
        }}>
          {/* Avatar & Basic Info */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            marginBottom: '30px'
          }}>
            {profile.profile_pic ? (
              <img 
                src={profile.profile_pic} 
                style={{ 
                  width: '140px', 
                  height: '140px', 
                  borderRadius: '50%', 
                  objectFit: 'cover', 
                  border: '5px solid #FE3C72',
                  marginBottom: '20px'
                }} 
                alt={profile.name}
              />
            ) : (
              <div style={{
                width: '140px',
                height: '140px',
                borderRadius: '50%',
                background: '#3a3a3a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '60px',
                border: '5px solid #FE3C72',
                marginBottom: '20px'
              }}>
                👤
              </div>
            )}
            
            <h1 style={{ 
              fontSize: '32px', 
              fontWeight: '800', 
              color: '#fff', 
              marginBottom: '8px' 
            }}>
              {profile.name}
            </h1>
            <p style={{ 
              color: '#8a8a8a', 
              fontSize: '18px', 
              marginBottom: '20px' 
            }}>
              @{profile.username}
            </p>
          
            {profile.biography && (
              <p style={{ 
                marginBottom: '20px', 
                color: '#b0b0b0',
                lineHeight: '1.6',
                maxWidth: '400px'
              }}>
                {profile.biography}
              </p>
            )}
          
            {profile.location && (
              <p style={{ 
                color: '#8a8a8a', 
                marginBottom: '25px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                📍 {profile.location}
              </p>
            )}
          
            {/* Stats */}
            <div style={{ 
              display: 'flex', 
              gap: '35px', 
              marginBottom: '25px',
              padding: '20px',
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '16px',
              width: '100%',
              maxWidth: '400px',
              justifyContent: 'center'
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  fontSize: '24px', 
                  fontWeight: '800', 
                  color: '#fff',
                  marginBottom: '5px'
                }}>
                  {profile.posts_count || 0}
                </div>
                <div style={{ 
                  color: '#8a8a8a', 
                  fontSize: '13px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  Gönderi
                </div>
              </div>
              <div style={{ width: '1px', background: 'rgba(255, 255, 255, 0.1)' }}></div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  fontSize: '24px', 
                  fontWeight: '800', 
                  color: '#fff',
                  marginBottom: '5px'
                }}>
                  {profile.followers_count || 0}
                </div>
                <div style={{ 
                  color: '#8a8a8a', 
                  fontSize: '13px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  Takipçi
                </div>
              </div>
              <div style={{ width: '1px', background: 'rgba(255, 255, 255, 0.1)' }}></div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  fontSize: '24px', 
                  fontWeight: '800', 
                  color: '#fff',
                  marginBottom: '5px'
                }}>
                  {profile.following_count || 0}
                </div>
                <div style={{ 
                  color: '#8a8a8a', 
                  fontSize: '13px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  Takip
                </div>
              </div>
            </div>
          
            {/* Action Button */}
            {isOwner ? (
              <button 
                onClick={() => setIsEditing(!isEditing)} 
                className="btn btn-primary"
                style={{ width: '100%', maxWidth: '300px' }}
              >
                {isEditing ? '✖ İptal' : '✏️ Profili Düzenle'}
              </button>
            ) : (
              <button 
                onClick={handleFollow} 
                className={profile.is_following ? 'btn btn-secondary' : 'btn btn-primary'}
                style={{ width: '100%', maxWidth: '300px' }}
              >
                {profile.is_following ? '✓ Takip Ediliyor' : '➕ Takip Et'}
              </button>
            )}
          </div>
        </div>
        
        {isEditing && (
          <EditProfileForm 
            profile={profile} 
            onSuccess={() => { 
              setIsEditing(false); 
              loadProfile(); 
            }} 
          />
        )}
      
        {/* Posts Grid */}
        <div style={{ marginTop: '40px' }}>
          <h2 style={{ 
            fontSize: '22px', 
            fontWeight: '700', 
            color: '#fff', 
            marginBottom: '25px',
            textAlign: 'center'
          }}>
            📸 Gönderiler
          </h2>
          
          {posts.length === 0 ? (
            <div style={{
              background: '#2a2a2a',
              borderRadius: '24px',
              padding: '60px 40px',
              textAlign: 'center',
              border: '1px solid rgba(255, 255, 255, 0.05)'
            }}>
              <div style={{ fontSize: '80px', marginBottom: '20px' }}>📭</div>
              <p style={{ color: '#8a8a8a', fontSize: '18px' }}>
                Henüz gönderi yok
              </p>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
              gap: '10px'
            }}>
              {posts.map((post: any) => (
                <div
                  key={post.id}
                  style={{
                    position: 'relative',
                    paddingBottom: '100%',
                    background: '#2a2a2a',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    cursor: 'pointer',
                    border: '1px solid rgba(255, 255, 255, 0.05)'
                  }}
                  onClick={() => {
                    const modal = document.getElementById(`modal-${post.id}`);
                    if (modal) modal.style.display = 'flex';
                  }}
                >
                  {post.image_url ? (
                    <img
                      src={post.image_url}
                      alt="Post"
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover'
                      }}
                    />
                  ) : (
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '48px'
                    }}>
                      📸
                    </div>
                  )}
                  
                  <div style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    padding: '12px',
                    background: 'linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent)',
                    display: 'flex',
                    gap: '15px',
                    fontSize: '13px',
                    color: '#fff'
                  }}>
                    <span>❤️ {post.likes_count || 0}</span>
                    <span>💬 {post.comments_count || 0}</span>
                  </div>

                  {/* Post Modal */}
                  <div
                    id={`modal-${post.id}`}
                    style={{
                      display: 'none',
                      position: 'fixed',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: 'rgba(0, 0, 0, 0.95)',
                      zIndex: 2000,
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: '20px'
                    }}
                    onClick={(e) => {
                      if (e.target === e.currentTarget) {
                        e.currentTarget.style.display = 'none';
                      }
                    }}
                  >
                    <div style={{
                      background: '#2a2a2a',
                      borderRadius: '24px',
                      maxWidth: '500px',
                      width: '100%',
                      maxHeight: '90vh',
                      overflow: 'auto',
                      border: '1px solid rgba(255, 255, 255, 0.1)'
                    }}>
                      {post.image_url && (
                        <img
                          src={post.image_url}
                          alt="Post"
                          style={{
                            width: '100%',
                            maxHeight: '500px',
                            objectFit: 'cover'
                          }}
                        />
                      )}
                      
                      <div style={{ padding: '25px' }}>
                        {/* User Info */}
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          marginBottom: '20px'
                        }}>
                          {profile.profile_pic ? (
                            <img
                              src={profile.profile_pic}
                              alt={profile.username}
                              style={{
                                width: '44px',
                                height: '44px',
                                borderRadius: '50%',
                                objectFit: 'cover',
                                border: '2px solid rgba(255, 255, 255, 0.2)'
                              }}
                            />
                          ) : (
                            <div style={{
                              width: '44px',
                              height: '44px',
                              borderRadius: '50%',
                              background: '#3a3a3a',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              border: '2px solid rgba(255, 255, 255, 0.2)'
                            }}>
                              👤
                            </div>
                          )}
                          <div>
                            <div style={{ fontSize: '18px', fontWeight: '700', color: '#fff' }}>
                              {profile.name}
                            </div>
                            <div style={{ fontSize: '13px', color: '#8a8a8a' }}>
                              @{profile.username}
                            </div>
                          </div>
                        </div>

                        {/* Content */}
                        {post.content && (
                          <p style={{
                            color: '#b0b0b0',
                            lineHeight: '1.6',
                            marginBottom: '15px'
                          }}>
                            {post.content}
                          </p>
                        )}

                        {/* Location */}
                        {post.location && (
                          <div style={{
                            color: '#8a8a8a',
                            fontSize: '14px',
                            marginBottom: '20px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                          }}>
                            📍 {post.location}
                          </div>
                        )}

                        {/* Actions */}
                        <div style={{
                          display: 'flex',
                          gap: '15px',
                          paddingTop: '20px',
                          borderTop: '1px solid rgba(255, 255, 255, 0.1)'
                        }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleLike(post.id, post.is_liked);
                            }}
                            style={{
                              flex: 1,
                              padding: '14px',
                              borderRadius: '12px',
                              border: 'none',
                              background: post.is_liked 
                                ? 'linear-gradient(135deg, #FE3C72 0%, #FF6036 100%)'
                                : '#3a3a3a',
                              color: 'white',
                              fontSize: '16px',
                              fontWeight: '700',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease'
                            }}
                          >
                            {post.is_liked ? '❤️' : '🤍'} {post.likes_count || 0}
                          </button>
                          <button
                            style={{
                              flex: 1,
                              padding: '14px',
                              borderRadius: '12px',
                              border: 'none',
                              background: '#3a3a3a',
                              color: 'white',
                              fontSize: '16px',
                              fontWeight: '700',
                              cursor: 'pointer'
                            }}
                          >
                            💬 {post.comments_count || 0}
                          </button>
                        </div>

                        {/* Close Button */}
                        <button
                          onClick={() => {
                            const modal = document.getElementById(`modal-${post.id}`);
                            if (modal) modal.style.display = 'none';
                          }}
                          style={{
                            width: '100%',
                            padding: '14px',
                            marginTop: '15px',
                            borderRadius: '12px',
                            border: 'none',
                            background: 'transparent',
                            color: '#8a8a8a',
                            fontSize: '16px',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          Kapat
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EditProfileForm({ profile, onSuccess }: { profile: any; onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    name: profile.name || '',
    biography: profile.biography || '',
    location: profile.location || ''
  });
  const [profilePic, setProfilePic] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(profile.profile_pic || null);
  const [updating, setUpdating] = useState(false);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setProfilePic(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdating(true);
    
    try {
      await profileAPI.updateProfile({
        name: formData.name,
        biography: formData.biography,
        location: formData.location,
        profile_pic: profilePic
      });
      
      alert('✅ Profil başarıyla güncellendi!');
      onSuccess();
    } catch (error: any) {
      console.error('Profil güncellenemedi:', error);
      const errorMessage = error.message || 'Profil güncellenemedi';
      alert(`❌ Hata: ${errorMessage}`);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div style={{
      background: '#2a2a2a',
      borderRadius: '24px',
      padding: '30px',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      marginBottom: '30px'
    }}>
      <h3 style={{ 
        fontSize: '22px', 
        fontWeight: '700', 
        color: '#fff', 
        marginBottom: '25px',
        textAlign: 'center'
      }}>
        ✏️ Profili Düzenle
      </h3>
      
      <form onSubmit={handleSubmit}>
        {/* Profile Picture */}
        <div style={{ marginBottom: '25px', textAlign: 'center' }}>
          <label htmlFor="profile-pic-upload" style={{ cursor: 'pointer' }}>
            {preview ? (
              <img
                src={preview}
                alt="Preview"
                style={{
                  width: '120px',
                  height: '120px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '4px solid #FE3C72',
                  marginBottom: '15px'
                }}
              />
            ) : (
              <div style={{
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                background: '#3a3a3a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '48px',
                border: '4px solid #FE3C72',
                margin: '0 auto 15px'
              }}>
                👤
              </div>
            )}
            <div style={{ 
              color: '#FE3C72', 
              fontSize: '14px', 
              fontWeight: '600' 
            }}>
              📸 Fotoğrafı Değiştir
            </div>
          </label>
          <input
            id="profile-pic-upload"
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            style={{ display: 'none' }}
          />
        </div>

        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Ad Soyad"
          className="input"
          style={{ marginBottom: '15px' }}
          required
        />

        <textarea
          value={formData.biography}
          onChange={(e) => setFormData({ ...formData, biography: e.target.value })}
          placeholder="Biyografi"
          className="input"
          style={{ minHeight: '100px', resize: 'vertical', marginBottom: '15px' }}
        />

        <input
          type="text"
          value={formData.location}
          onChange={(e) => setFormData({ ...formData, location: e.target.value })}
          placeholder="📍 Konum"
          className="input"
          style={{ marginBottom: '20px' }}
        />

        <button
          type="submit"
          disabled={updating}
          className="btn btn-primary"
          style={{
            width: '100%',
            opacity: updating ? 0.5 : 1,
            cursor: updating ? 'not-allowed' : 'pointer'
          }}
        >
          {updating ? (
            <>
              <span className="loading" style={{ width: '20px', height: '20px' }}></span>
              Kaydediliyor...
            </>
          ) : (
            '💾 Kaydet'
          )}
        </button>
      </form>
      
      {/* Delete Account Section */}
      <div style={{
        marginTop: '30px',
        paddingTop: '30px',
        borderTop: '1px solid rgba(255, 255, 255, 0.05)'
      }}>
        <h4 style={{
          fontSize: '16px',
          fontWeight: '600',
          color: '#ff4444',
          marginBottom: '15px'
        }}>
          🚨 Tehlikeli Alan
        </h4>
        <p style={{
          fontSize: '14px',
          color: '#8a8a8a',
          marginBottom: '15px',
          lineHeight: '1.5'
        }}>
          Hesabını sildiğinde tüm gönderilerin, beğenilerin ve takipçilerin kalıcı olarak silinecek. Bu işlem geri alınamaz.
        </p>
        <button
          onClick={async () => {
            if (window.confirm('⚠️ Hesabını kalıcı olarak silmek istediğinden emin misin?\n\nBu işlem geri alınamaz ve:\n• Tüm gönderilerini\n• Tüm beğenilerini\n• Tüm takipçilerini\n• Tüm aktivite geçmişini\n\nkalıcı olarak silecek.')) {
              try {
                await profileAPI.deleteAccount();
              } catch (error) {
                console.error('Hesap silinemedi:', error);
                alert('Hesap silinemedi. Lütfen tekrar deneyin.');
              }
            }
          }}
          className="btn"
          style={{
            width: '100%',
            background: 'rgba(255, 68, 68, 0.1)',
            color: '#ff4444',
            border: '1px solid rgba(255, 68, 68, 0.3)',
            fontWeight: '600'
          }}
        >
          🗑️ Hesabı Kalıcı Olarak Sil
        </button>
      </div>
    </div>
  );
}
