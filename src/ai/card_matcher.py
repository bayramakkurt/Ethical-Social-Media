import cv2
import numpy as np
from PIL import Image
import io

class CardMatcher:
    """
    Kart eşleştirme sınıfı - Ölçek ve açı bağımsız görüntü eşleştirme
    SIFT veya ORB algoritması kullanarak kart görsellerini karşılaştırır
    """
    
    def __init__(self, algorithm="orb"):
        """
        algorithm: "sift" veya "orb" 
        ORB daha hızlı, SIFT daha hassas (ancak patent kısıtlaması olabilir)
        """
        self.algorithm = algorithm.lower()
        
        if self.algorithm == "sift":
            try:
                self.detector = cv2.SIFT_create()
            except:
                print("SIFT kullanılamıyor, ORB'ye geçiliyor...")
                self.algorithm = "orb"
                self.detector = cv2.ORB_create(nfeatures=2000)
        else:
            self.detector = cv2.ORB_create(nfeatures=2000)
        
        # Matcher (eşleştirici)
        if self.algorithm == "sift":
            self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        else:
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        
        print(f"CardMatcher başlatıldı - Algoritma: {self.algorithm.upper()}")
    
    def _preprocess_image(self, image):
        """
        Görseli işleme için hazırlar
        PIL Image veya numpy array kabul eder
        """
        # PIL Image ise numpy array'e çevir
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        # RGB ise BGR'ye çevir (OpenCV için)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Gri tonlamaya çevir
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Kontrast iyileştirme (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        return enhanced
    
    def extract_features(self, image):
        """
        Görselden özellik çıkarımı yapar
        Returns: (keypoints, descriptors)
        """
        processed = self._preprocess_image(image)
        keypoints, descriptors = self.detector.detectAndCompute(processed, None)
        return keypoints, descriptors
    
    def match_cards(self, card_image1, card_image2, threshold=0.75):
        """
        İki kart görselini karşılaştırır
        
        Parameters:
        - card_image1: İlk kart görseli (PIL Image, numpy array veya base64)
        - card_image2: İkinci kart görseli
        - threshold: Eşleşme eşiği (0.0-1.0, düşük değer = daha sıkı kontrol)
        
        Returns:
        {
            "is_match": bool,
            "confidence": float (0-100),
            "good_matches": int,
            "total_matches": int,
            "similarity_score": float
        }
        """
        try:
            # Base64 string kontrolü ve dönüşümü
            import base64
            
            for idx, img in enumerate([card_image1, card_image2]):
                if isinstance(img, str):
                    if img.startswith('data:image'):
                        img = img.split('base64,')[1] if 'base64,' in img else img
                    
                    image_bytes = base64.b64decode(img)
                    img = Image.open(io.BytesIO(image_bytes))
                    
                    if idx == 0:
                        card_image1 = img
                    else:
                        card_image2 = img
            
            # Özellik çıkarımı
            kp1, desc1 = self.extract_features(card_image1)
            kp2, desc2 = self.extract_features(card_image2)
            
            if desc1 is None or desc2 is None:
                return {
                    "is_match": False,
                    "confidence": 0.0,
                    "error": "Özellikleri çıkarılamadı. Görsel kalitesi düşük olabilir."
                }
            
            # Eşleştirme
            if self.algorithm == "sift":
                # SIFT için KNN matcher
                matches = self.matcher.knnMatch(desc1, desc2, k=2)
                
                # Lowe's ratio test
                good_matches = []
                for match_pair in matches:
                    if len(match_pair) == 2:
                        m, n = match_pair
                        if m.distance < threshold * n.distance:
                            good_matches.append(m)
            else:
                # ORB için KNN matcher
                matches = self.matcher.knnMatch(desc1, desc2, k=2)
                
                good_matches = []
                for match_pair in matches:
                    if len(match_pair) == 2:
                        m, n = match_pair
                        if m.distance < threshold * n.distance:
                            good_matches.append(m)
            
            total_features = min(len(kp1), len(kp2))
            match_ratio = len(good_matches) / total_features if total_features > 0 else 0
            
            # Benzerlik skoru hesaplama
            similarity_score = match_ratio * 100
            
            # Eşleşme kararı (en az 30 iyi eşleşme VE %20 benzerlik)
            is_match = len(good_matches) >= 30 and similarity_score >= 20
            
            return {
                "is_match": is_match,
                "confidence": round(similarity_score, 2),
                "good_matches": len(good_matches),
                "total_matches": len(matches) if self.algorithm == "sift" else len(matches),
                "similarity_score": round(similarity_score, 2),
                "algorithm": self.algorithm.upper()
            }
        
        except Exception as e:
            return {
                "is_match": False,
                "confidence": 0.0,
                "error": str(e)
            }
