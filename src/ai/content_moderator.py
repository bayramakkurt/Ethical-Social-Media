from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
import sys

class ContentModerator:
    def __init__(self):
        """
        Modeli hafızaya yükler. Bu işlem program açılışında bir kez yapılır.
        """
        # 1. Cihaz Seçimi
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"ContentModerator Başlatılıyor... Cihaz: {self.device.upper()}")

        # 2. Modeli Yükle
        try:
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True).to(self.device)
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            print("Model başarıyla yüklendi ve hazır.")
        except Exception as e:
            print(f"Model yüklenirken kritik hata: {e}")
            sys.exit()

        # 3. Etiket Tanımları (Optimize edilmiş liste)
        self.labels = [
            # ---------------------------------------------------------
            # [GRUP A] ŞİDDET, KAN VE VAHŞET (Indices: 0-4)
            # ---------------------------------------------------------
            "physical violence, street fighting, or people punching each other", # 0: Kavga
            "real human blood, bleeding wound, or gore scene",                  # 1: Gerçek kan/yara
            "a dead body, corpse, or murder scene",                             # 2: Ceset
            "severe car accident with injuries",                                # 3: Ağır kaza
            "torture, suffering, or disturbing content",                        # 4: İşkence

            # ---------------------------------------------------------
            # [GRUP B] CİNSELLİK VE ÇIPLAKLIK (Indices: 5-9)
            # ---------------------------------------------------------
            "explicit nudity, pornography, or sexual intercourse",              # 5: Porno
            "exposed genitals, penis, or vagina",                               # 6: Cinsel organ
            "a person in sexy lingerie or lace underwear",                      # 7: İç çamaşırı (Dantelli vs.)
            "erotic pose or sexually suggestive content",                       # 8: Erotik
            "cartoon hentai or animated pornography",                           # 9: Hentai

            # ---------------------------------------------------------
            # [GRUP C] SİLAH VE TEHDİT (Indices: 10-13)
            # ---------------------------------------------------------
            "a person holding a real firearm, pistol, or rifle",                # 10: Ateşli Silah (Elde)
            "a person holding a knife or dagger in a threatening way",          # 11: Bıçak (Tehditkar)
            "illegal drugs, cocaine lines, or heroin syringe",                  # 12: Uyuşturucu
            "a terrorist, militia, or war zone",                                # 13: Terör

            # ---------------------------------------------------------
            # [GRUP D] NEFRET VE HAKARET (Indices: 14-15)
            # ---------------------------------------------------------
            "a middle finger gesture",                                          # 14: Orta parmak
            "hate symbol, swastika, or racism",                                 # 15: Nefret sembolü

            # =========================================================
            # [GRUP E] GÜVENLİ BÖLGE & TUZAKLAR (DECOYS) (Indices: 16+)
            # Burası modelin yanlış alarm vermesini önleyen "Benzeyen ama Güvenli" şeylerdir.
            # =========================================================
            
            # --- RENK YANILGISINI ÖNLEYENLER (Kan sanılmasın diye) ---
            "a red sports car or red vehicle",                                  # 16: Kırmızı Araba
            "red roses, flowers, or tulips",                                    # 17: Kırmızı Çiçek
            "red paint, art supplies, or spilled ketchup",                      # 18: Boya/Salça
            "a person wearing a red dress or red t-shirt",                      # 19: Kırmızı Kıyafet
            "raw meat or steak for cooking",                                    # 20: Çiğ et (Yemek)
            
            # --- OBJE YANILGISINI ÖNLEYENLER (Silah sanılmasın diye) ---
            "a person holding a black smartphone or taking a selfie",           # 21: Telefon
            "a person holding a wallet or credit card",                         # 22: Cüzdan
            "a person holding a remote control or game controller",             # 23: Kumanda
            "kitchen knife on a cutting board with vegetables",                 # 24: Mutfak bıçağı (Yemek yaparken)
            "a toy water gun or plastic toy",                                   # 25: Oyuncak silah
            "medical vaccine injection or doctor visit",                        # 26: Aşı (Uyuşturucu sanılmasın)

            # --- TEN RENGİ/TEMAS YANILGISINI ÖNLEYENLER (NSFW/Şiddet sanılmasın diye) ---
            "people hugging, wrestling sport, or dancing",                      # 27: Temas (Şiddet değil)
            "a person wearing swimwear, bikini, or gym shorts at beach",        # 28: Mayo (Porno değil)
            "a shirtless man doing sports or swimming",                         # 29: Üstsüz sporcu
            "a breastfeeding mother or baby care",                              # 30: Emzirme/Bebek
            "marble statue or artistic painting",                               # 31: Sanat heykeli

            # --- GENEL GÜVENLİ ---
            "a standard portrait or group selfie",                              # 32: Normal İnsan
            "landscape, nature, or city street",                                # 33: Manzara
            "a photo of documents, text, or screenshots",                       # 34: Belge
            "food, drinks, or restaurant scene"                                 # 35: Yemek
        ]

        # Yasaklı Kategorilerin İndeks Haritası
        self.category_map = {
            "violence": [0, 1, 2, 3, 4],
            "nsfw":     [5, 6, 7, 8, 9],
            "weapon":   [10, 11, 12, 13],
            "hate":     [14, 15]
        }
        
        # Güvenli listenin başladığı indeks (16 ve sonrası HEPSİ GÜVENLİDİR)
        self.safe_start_index = 16
        
        # Yasaklı indekslerin birleşik listesi
        self.forbidden_indices = (
            self.category_map["violence"] + 
            self.category_map["nsfw"] + 
            self.category_map["weapon"] + 
            self.category_map["hate"]
        )

    def analyze_image(self, image_source):
        """
        Görseli analiz eder.
        Parametre: image_source -> Dosya yolu (str) veya PIL Image objesi olabilir.
        Dönüş: { 'label': str, 'score': float, 'is_shareable': bool }
        """
        # Gelen veri dosya yolu mu yoksa resim objesi mi kontrol et
        try:
            if isinstance(image_source, str):
                image = Image.open(image_source)
            else:
                image = image_source
        except Exception as e:
            return {"error": f"Resim açılamadı: {e}", "is_shareable": False}

        # Analiz İşlemi
        inputs = self.processor(text=self.labels, images=image, return_tensors="pt", padding=True).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Olasılıkları hesapla
        probs = outputs.logits_per_image.softmax(dim=1)
        probs_np = probs.cpu().numpy()[0]

        # En yüksek skoru bul
        max_index = probs_np.argmax()
        max_score = probs_np[max_index] * 100
        detected_label = self.labels[max_index]

        # --- KARAR MEKANİZMASI ---
        is_shareable = True
        detected_category = "safe"
        
        # Hangi kategoriye ait olduğunu bul
        def get_category_name(index):
            for cat_name, indices in self.category_map.items():
                if index in indices:
                    return cat_name
            return "safe"
        
        # 1. Kural: En yüksek skor yasaklı kategoride mi?
        if max_index in self.forbidden_indices:
            is_shareable = False
            detected_category = get_category_name(max_index)
        
        # 2. Kural: Herhangi bir yasaklı kategori %50'yi geçti mi? (Çoklu kontrol)
        # Örn: Hem silah hem kan olabilir.
        for i in self.forbidden_indices:
            if probs_np[i] > 0.50:
                is_shareable = False
                detected_label = self.labels[i] # Sebebini yasaklı olanla güncelle
                max_score = probs_np[i] * 100
                detected_category = get_category_name(i)
                break
        
        # Türkçe kategori isimleri
        category_names_tr = {
            "violence": "Şiddet/Kan",
            "nsfw": "Cinsel İçerik",
            "weapon": "Silah/Suç",
            "hate": "Nefret/Hakaret",
            "safe": "Güvenli"
        }

        # Sonuç Sözlüğü Döndür
        return {
            "label": detected_label,                              # Tespit edilen etiket (İngilizce)
            "category": detected_category,                         # Kategori (violence, nsfw, weapon, hate, safe)
            "category_tr": category_names_tr[detected_category],  # Kategori (Türkçe)
            "score": round(max_score, 2),                         # Yüzdelik oran (Örn: 98.5)
            "is_shareable": is_shareable,                         # True (Paylaşılabilir) / False (Engelle)
            "all_scores": probs_np                                # (Opsiyonel) Tüm skorlar gerekirse diye
        }