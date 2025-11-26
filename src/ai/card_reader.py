import easyocr
import torch
import numpy as np
from facenet_pytorch import MTCNN
from PIL import Image

class SpatialCardReader:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"SpatialCardReader Final v3 Başlatılıyor... Cihaz: {str(self.device).upper()}")

        self.reader = easyocr.Reader(['tr', 'en'], gpu=(self.device.type == 'cuda'))
        self.mtcnn = MTCNN(keep_all=False, device=self.device, select_largest=True, margin=0)
        
        print("✅ Sistem Hazır.")

    def analyze_card(self, image_source, face_margin=0.5):
        result = {
            "parsed_data": {},
            "face_found": False,
            "face_image": None,
            "all_text_boxes": [],
            "error": None
        }

        try:
            # 1. Görsel Hazırlığı
            if isinstance(image_source, str):
                img = Image.open(image_source).convert('RGB')
            else:
                img = image_source
            
            width, height = img.size
            img_np = np.array(img)

            # 2. OCR İşlemi
            raw_data = self.reader.readtext(img_np, detail=1)
            result["all_text_boxes"] = raw_data

            # 3. Yüz Tespiti ve Genişletme
            boxes, _ = self.mtcnn.detect(img)
            face_bottom_y = 0
            
            if boxes is not None:
                box = boxes[0]
                x1, y1, x2, y2 = box
                
                # Genişletme
                w_face = x2 - x1
                h_face = y2 - y1
                m_x = w_face * face_margin
                m_y = h_face * face_margin
                
                nx1 = max(0, int(x1 - m_x))
                ny1 = max(0, int(y1 - m_y))
                nx2 = min(width, int(x2 + m_x))
                ny2 = min(height, int(y2 + m_y))
                
                face_crop = img.crop((nx1, ny1, nx2, ny2))
                result["face_image"] = face_crop
                result["face_found"] = True
                face_bottom_y = y2 

            # 4. Satır Birleştirme
            merged_lines = self._merge_text_lines(raw_data)

            # --- 5. VERİ ÇIKARMA ---
            parsed = {
                "Sirket": None,
                "Isim_Soyisim": None,
                "Unvan": None,
                "ID_Sicil": None,
                "Email": None,
                "Konum": None,
                "Dogum_Tarihi": None,
                "Cinsiyet": None
            }

            # --- A. Şirket Adı (GÜNCELLENMİŞ MANTIK) ---
            # Logo yazısını atlayıp, sadece şirket adını almak için strateji:
            # 1. Üst %25'lik alandaki satırları topla.
            # 2. Y koordinatına göre sırala.
            # 3. En alttaki (yani yüze en yakın olan) satırı "Şirket Adı" olarak seç.
            
            header_candidates = []
            for line_bbox, line_text in merged_lines:
                center_y = (line_bbox[0][1] + line_bbox[2][1]) / 2
                
                # Kartın üst %25'lik kısmında mı?
                if center_y < (height * 0.25):
                    header_candidates.append((center_y, line_text))
            
            if header_candidates:
                # Y eksenine göre sırala (Küçükten büyüğe -> Yukarıdan aşağıya)
                header_candidates.sort(key=lambda x: x[0])
                
                # Eğer birden fazla satır varsa (Örn: 1. Logo Text, 2. Şirket Adı)
                # Biz en sondakini (en alttakini) alıyoruz.
                parsed["Sirket"] = header_candidates[-1][1]
            

            # B. İsim ve Unvan
            if result["face_found"]:
                candidate_lines = []
                for line_bbox, line_text in merged_lines:
                    center_y = (line_bbox[0][1] + line_bbox[2][1]) / 2
                    if center_y > face_bottom_y:
                        if center_y < face_bottom_y + (height * 0.3):
                            candidate_lines.append(line_text)
                
                if len(candidate_lines) >= 1:
                    parsed["Isim_Soyisim"] = candidate_lines[0]
                if len(candidate_lines) >= 2:
                    parsed["Unvan"] = candidate_lines[1]

            # C. Etiket Bazlı Arama
            anchors = {
                "ID / SICIL NO": "ID_Sicil", "EMAIL": "Email", "KONUM": "Konum",
                "DOĞUM T.": "Dogum_Tarihi", "CINSIYET": "Cinsiyet",
                "DOĞUM": "Dogum_Tarihi", "ID": "ID_Sicil"
            }

            for bbox, text, conf in raw_data:
                clean_text = text.upper().strip()
                found_key = None
                for anchor_text, key_name in anchors.items():
                    if anchor_text in clean_text:
                        found_key = key_name
                        break
                
                if found_key:
                    anchor_bottom_y = bbox[2][1]
                    anchor_center_x = (bbox[0][0] + bbox[1][0]) / 2
                    best_match = None
                    min_dist = float('inf')

                    for val_bbox, val_text, val_conf in raw_data:
                        if val_bbox == bbox: continue
                        val_top_y = val_bbox[0][1]
                        val_center_x = (val_bbox[0][0] + val_bbox[1][0]) / 2

                        if val_top_y > anchor_bottom_y:
                            if abs(val_center_x - anchor_center_x) < 200:
                                y_dist = val_top_y - anchor_bottom_y
                                if y_dist < 120:
                                    if y_dist < min_dist:
                                        min_dist = y_dist
                                        best_match = val_text
                    
                    if best_match:
                        if parsed[found_key] is None or len(best_match) > len(parsed[found_key]):
                            parsed[found_key] = best_match

            result["parsed_data"] = parsed
            return result

        except Exception as e:
            result["error"] = str(e)
            return result

    def _merge_text_lines(self, raw_data, y_threshold=20): # Threshold biraz artırıldı
        sorted_data = sorted(raw_data, key=lambda r: (r[0][0][1] + r[0][2][1]) / 2)
        merged_lines = []
        current_line_items = []
        
        if not sorted_data: return []

        current_line_items.append(sorted_data[0])
        for i in range(1, len(sorted_data)):
            item = sorted_data[i]
            prev_item = current_line_items[0]
            cy_current = (item[0][0][1] + item[0][2][1]) / 2
            cy_prev = (prev_item[0][0][1] + prev_item[0][2][1]) / 2
            
            if abs(cy_current - cy_prev) < y_threshold:
                current_line_items.append(item)
            else:
                merged_lines.append(self._process_single_line(current_line_items))
                current_line_items = [item]
        
        if current_line_items:
            merged_lines.append(self._process_single_line(current_line_items))
        return merged_lines

    def _process_single_line(self, items):
        items.sort(key=lambda r: r[0][0][0])
        full_text = " ".join([item[1] for item in items])
        min_x = min([item[0][0][0] for item in items])
        min_y = min([item[0][0][1] for item in items])
        max_x = max([item[0][2][0] for item in items])
        max_y = max([item[0][2][1] for item in items])
        new_bbox = [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]
        return (new_bbox, full_text)