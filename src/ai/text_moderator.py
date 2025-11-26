import warnings
import torch
import sys
from transformers import AutoModelForSequenceClassification, AutoTokenizer

warnings.filterwarnings("ignore", category=UserWarning)

class TextModerator:
    def __init__(self, model_name: str = "thothai/turkce-kufur-tespiti"):
        """
        Token parametresi kaldırıldı. Sistemdeki kayıtlı girişi kullanır.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"TextModerator Başlatılıyor... Cihaz: {self.device}")

        try:
            # Token parametresi yerine sistemdeki login'i kullanıyoruz.
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name, 
                use_safetensors=True
            ).to(self.device)
            
            self.model.eval()
            print("✅ Metin Modeli Başarıyla Yüklendi!")
            
        except OSError as e:
            print("\n❌ HATA: Model indirilemedi veya yetki hatası.")
            print("ÇÖZÜM: Lütfen terminale 'huggingface-cli login' yazıp token'ınızı girin.")
            print(f"Teknik Hata: {e}")
            sys.exit()
        except Exception as e:
            print(f"Beklenmeyen bir hata: {e}")
            sys.exit()

    def analyze_text(self, text: str) -> dict:
        if not text or text.strip() == "":
            return {"text": "", "is_toxic": False, "score": 0.0, "label": "BOŞ"}

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
            pred_class_id = torch.argmax(logits, dim=1).item()
            confidence = probs[0][pred_class_id].item() * 100

        # Modelde 0 = KÜFÜR, 1 = TEMİZ
        is_toxic = (pred_class_id == 0)
        label_text = "KÜFÜRLÜ" if is_toxic else "TEMİZ"

        return {
            "is_toxic": is_toxic,
            "score": round(confidence, 2),
            "label": label_text
        }