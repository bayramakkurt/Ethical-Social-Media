import { useState, useEffect } from 'react';
import { postAPI, getCurrentUser } from '../lib/api';

export default function Feed() {
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  useEffect(() => {
    const user = getCurrentUser();
    console.log('Current user data:', user);
    setCurrentUser(user);
    if (!user) {
      window.location.href = '/login';
      return;
    }
    loadFeed();
  }, []);
  
  const loadFeed = async () => {
    try {
      const data = await postAPI.getFeed(1, 50);
      console.log('Feed data:', data);
      setPosts(data);
    } catch (error) {
      console.error('Feed yüklenemedi:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (postId: number, isLiked: boolean) => {
    try {
      if (isLiked) {
        await postAPI.unlikePost(postId);
      } else {
        await postAPI.likePost(postId);
      }
      await loadFeed();
    } catch (error) {
      console.error('Beğeni hatası:', error);
    }
  };

  const handleDelete = async (postId: number) => {
    try {
      await postAPI.deletePost(postId);
      await loadFeed();
    } catch (error) {
      console.error('Silme hatası:', error);
      alert('Gönderi silinemedi');
    }
  };

  const handleSearch = async (e: any) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      loadFeed();
      return;
    }
    
    try {
      setLoading(true);
      const data = await postAPI.searchPosts(searchQuery);
      setPosts(data);
    } catch (error) {
      console.error('Arama hatası:', error);
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%)',
      paddingBottom: '100px'
    }}>
      {/* Top Bar */}
      <div style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: 'rgba(26, 26, 26, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        padding: '15px 20px'
      }}>
        <div style={{
          maxWidth: '600px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '15px'
        }}>
          <div style={{ 
            fontSize: '28px', 
            fontWeight: '800', 
            color: '#FE3C72',
            letterSpacing: '-1px',
            flexShrink: 0
          }}>
            Social
          </div>

          {/* Search Bar */}
          <form onSubmit={handleSearch} style={{ flex: 1, display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="🔍 #hashtag ara..."
              style={{
                flex: 1,
                padding: '10px 15px',
                background: '#2a2a2a',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '25px',
                color: '#fff',
                fontSize: '14px',
                outline: 'none'
              }}
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('');
                  loadFeed();
                }}
                style={{
                  padding: '10px 20px',
                  background: '#3a3a3a',
                  border: 'none',
                  borderRadius: '25px',
                  color: '#8a8a8a',
                  fontSize: '14px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                ✕
              </button>
            )}
          </form>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexShrink: 0 }}>
            <button 
              onClick={() => setShowCreatePost(true)}
              style={{
                background: 'linear-gradient(135deg, #FE3C72 0%, #FF6036 100%)',
                border: 'none',
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                fontSize: '20px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(254, 60, 114, 0.4)'
              }}
            >
              ➕
            </button>
            <a href={`/profile/${currentUser?.username}`}>
              {currentUser?.profile_pic ? (
                <img 
                  src={currentUser.profile_pic} 
                  alt="Profile" 
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: '2px solid #FE3C72',
                    cursor: 'pointer'
                  }}
                />
              ) : (
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: '#3a3a3a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px',
                  border: '2px solid #FE3C72',
                  cursor: 'pointer'
                }}>
                  👤
                </div>
              )}
            </a>
          </div>
        </div>
      </div>

      {/* Feed Container */}
      <div style={{
        maxWidth: '600px',
        margin: '0 auto',
        padding: '20px'
      }}>
        {posts.length === 0 ? (
          <div style={{
            background: '#2a2a2a',
            borderRadius: '24px',
            padding: '60px 40px',
            textAlign: 'center',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            marginTop: '40px'
          }}>
            <div style={{ fontSize: '80px', marginBottom: '20px' }}>
              {searchQuery ? '🔍' : '📭'}
            </div>
            <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#fff', marginBottom: '10px' }}>
              {searchQuery ? 'Sonuç Bulunamadı' : 'Henüz Gönderi Yok'}
            </h2>
            <p style={{ fontSize: '16px', color: '#8a8a8a' }}>
              {searchQuery ? 'Farklı bir arama yapmayı dene' : 'İlk gönderiyi sen oluştur!'}
            </p>
            {!searchQuery && (
              <button 
                onClick={() => setShowCreatePost(true)}
                className="btn btn-primary"
                style={{ marginTop: '25px' }}
              >
                ➕ Gönderi Oluştur
              </button>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {posts.map((post: any) => (
              <PostCard 
                key={post.id} 
                post={post} 
                onLike={handleLike}
                currentUserId={currentUser?.id}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Post Modal */}
      {showCreatePost && (
        <CreatePostModal 
          onClose={() => setShowCreatePost(false)}
          onSuccess={() => {
            setShowCreatePost(false);
            loadFeed();
          }}
        />
      )}
    </div>
  );
}

function PostCard({ post, onLike, currentUserId, onDelete }: { 
  post: any; 
  onLike: (id: number, isLiked: boolean) => void; 
  currentUserId: number;
  onDelete?: (id: number) => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  
  return (
    <div style={{
      background: '#2a2a2a',
      borderRadius: '24px',
      overflow: 'hidden',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      position: 'relative'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
      }}>
        <a 
          href={`/profile/${post.user?.username}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            textDecoration: 'none',
            color: 'inherit'
          }}
        >
          {post.user?.profile_pic ? (
            <img
              src={post.user.profile_pic}
              alt={post.user.username}
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '50%',
                objectFit: 'cover',
                border: '2px solid rgba(255, 255, 255, 0.1)'
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
              border: '2px solid rgba(255, 255, 255, 0.1)',
              fontSize: '20px'
            }}>
              👤
            </div>
          )}
          <div>
            <div style={{
              fontSize: '16px',
              fontWeight: '700',
              color: '#fff',
              marginBottom: '2px'
            }}>
              {post.user?.full_name || 'Kullanıcı'}
            </div>
            <div style={{
              fontSize: '13px',
              color: '#8a8a8a'
            }}>
              @{post.user?.username || 'user'}
            </div>
          </div>
        </a>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {post.location && (
            <div style={{
              fontSize: '12px',
              color: '#8a8a8a',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              📍 {post.location}
            </div>
          )}
          
          {/* Menu button for own posts */}
          {currentUserId === post.author_id && onDelete && (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowMenu(!showMenu)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#8a8a8a',
                  fontSize: '24px',
                  cursor: 'pointer',
                  padding: '4px 8px'
                }}
              >
                ⋮
              </button>
              
              {showMenu && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  background: '#3a3a3a',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  overflow: 'hidden',
                  marginTop: '8px',
                  minWidth: '150px',
                  zIndex: 10
                }}>
                  <button
                    onClick={() => {
                      if (confirm('Bu gönderiyi silmek istediğinize emin misiniz?')) {
                        onDelete(post.id);
                      }
                      setShowMenu(false);
                    }}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      background: 'transparent',
                      border: 'none',
                      color: '#FE3C72',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'background 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(254, 60, 114, 0.1)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    🗑️ Sil
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Image */}
      {post.image_url && (
        <img
          src={post.image_url}
          alt="Post"
          style={{
            width: '100%',
            maxHeight: '600px',
            objectFit: 'cover',
            display: 'block'
          }}
        />
      )}

      {/* Actions */}
      <div style={{
        padding: '16px 20px'
      }}>
        <div style={{
          display: 'flex',
          gap: '20px',
          marginBottom: '12px'
        }}>
          <button
            onClick={() => onLike(post.id, post.is_liked)}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '24px',
              padding: '0',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: post.is_liked ? '#FE3C72' : '#8a8a8a',
              transition: 'all 0.2s ease'
            }}
          >
            {post.is_liked ? '❤️' : '🤍'}
            <span style={{ 
              fontSize: '15px', 
              fontWeight: '600',
              color: post.is_liked ? '#FE3C72' : '#8a8a8a'
            }}>
              {post.likes_count || 0}
            </span>
          </button>
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: '#8a8a8a',
            fontSize: '24px'
          }}>
            💬
            <span style={{ fontSize: '15px', fontWeight: '600' }}>
              {post.comments_count || 0}
            </span>
          </div>
        </div>

        {/* Content */}
        {post.content && (
          <p style={{
            color: '#fff',
            fontSize: '15px',
            lineHeight: '1.5',
            margin: 0,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}>
            {post.content}
          </p>
        )}

        {/* Timestamp */}
        <div style={{
          fontSize: '12px',
          color: '#666',
          marginTop: '12px'
        }}>
          {new Date(post.created_at).toLocaleDateString('tr-TR', { 
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  );
}

function CreatePostModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [content, setContent] = useState('');
  const [location, setLocation] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!imageFile && !content.trim()) return;

    setUploading(true);
    try {
      await postAPI.createPost({
        content: content.trim(),
        location: location.trim(),
        image: imageFile
      });
      onSuccess();
    } catch (error: any) {
      console.error('Gönderi oluşturma hatası:', error);
      
      // Detaylı hata mesajını göster
      let errorMessage = 'Gönderi oluşturulamadı';
      
      if (error.message) {
        try {
          // JSON parse edebiliyorsak detaylı mesaj al
          const errorData = typeof error.message === 'string' ? JSON.parse(error.message) : error.message;
          
          if (errorData.detail) {
            if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            } else if (errorData.detail.message) {
              // Backend'den gelen formatlanmış mesajı direkt kullan
              errorMessage = errorData.detail.message;
            }
          }
        } catch (parseError) {
          // Parse edilemezse error.message'ı direkt kullan
          errorMessage = error.message;
        }
      }
      
      alert(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.9)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      padding: '20px'
    }}
    onClick={onClose}
    >
      <div 
        style={{
          background: '#2a2a2a',
          borderRadius: '24px',
          maxWidth: '500px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h2 style={{
            fontSize: '22px',
            fontWeight: '700',
            color: '#fff',
            margin: 0
          }}>
            Yeni Gönderi
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#8a8a8a',
              fontSize: '28px',
              cursor: 'pointer',
              padding: '0',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ padding: '20px' }}>
          {imagePreview && (
            <div style={{
              marginBottom: '20px',
              position: 'relative',
              borderRadius: '16px',
              overflow: 'hidden'
            }}>
              <img
                src={imagePreview}
                alt="Preview"
                style={{
                  width: '100%',
                  maxHeight: '400px',
                  objectFit: 'cover'
                }}
              />
              <button
                type="button"
                onClick={() => {
                  setImageFile(null);
                  setImagePreview(null);
                }}
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  background: 'rgba(0, 0, 0, 0.7)',
                  border: 'none',
                  color: 'white',
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  cursor: 'pointer',
                  fontSize: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ✕
              </button>
            </div>
          )}

          <div style={{ marginBottom: '20px' }}>
            <label
              htmlFor="image-upload"
              style={{
                display: 'block',
                padding: '40px 20px',
                border: '2px dashed rgba(254, 60, 114, 0.3)',
                borderRadius: '16px',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                background: imagePreview ? 'transparent' : 'rgba(254, 60, 114, 0.05)'
              }}
              onMouseOver={(e) => {
                if (!imagePreview) {
                  e.currentTarget.style.borderColor = '#FE3C72';
                  e.currentTarget.style.background = 'rgba(254, 60, 114, 0.1)';
                }
              }}
              onMouseOut={(e) => {
                if (!imagePreview) {
                  e.currentTarget.style.borderColor = 'rgba(254, 60, 114, 0.3)';
                  e.currentTarget.style.background = 'rgba(254, 60, 114, 0.05)';
                }
              }}
            >
              <div style={{ fontSize: '48px', marginBottom: '10px' }}>📸</div>
              <div style={{ color: '#8a8a8a', fontSize: '14px' }}>
                {imagePreview ? 'Değiştirmek için tıkla' : 'Fotoğraf yükle'}
              </div>
            </label>
            <input
              id="image-upload"
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              style={{ display: 'none' }}
            />
          </div>

          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Bir şeyler yaz... (#hashtag kullanabilirsin)"
            className="input"
            style={{
              minHeight: '120px',
              resize: 'vertical',
              marginBottom: '15px'
            }}
          />

          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="📍 Konum ekle (opsiyonel)"
            className="input"
            style={{ marginBottom: '20px' }}
          />

          <button
            type="submit"
            disabled={uploading || (!imageFile && !content.trim())}
            className="btn btn-primary"
            style={{
              width: '100%',
              opacity: uploading || (!imageFile && !content.trim()) ? 0.5 : 1,
              cursor: uploading || (!imageFile && !content.trim()) ? 'not-allowed' : 'pointer'
            }}
          >
            {uploading ? (
              <>
                <span className="loading" style={{ width: '20px', height: '20px' }}></span>
                Yükleniyor...
              </>
            ) : (
              'Paylaş'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
