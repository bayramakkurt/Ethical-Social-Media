from card_reader import SpatialCardReader
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

def visualize_complete_result(result):
    """
    Hem kartı, hem kırpılan yüzü, hem de verileri gösterir.
    """
    parsed = result["parsed_data"]
    
    # Grafik Alanı Oluştur (1 satır, 2 sütun: Solda Kart, Sağda Veriler+Yüz)
    fig = plt.figure(figsize=(14, 8))
    
    # --- SOL TARAF: KART ---
    ax1 = fig.add_subplot(1, 2, 1)
    if result.get("all_text_boxes"): 
        # Arka planda orijinal resim olmalı, bunu main'den çekmemiz lazım ama 
        # kolaylık olsun diye spatial reader'ın içine kaydetmedik, tekrar açalım:
        pass # (Burada resim path'i lazım, main'de halledeceğiz)

    ax1.set_title("Kart Analizi", fontsize=14)
    ax1.axis('off')

    # --- SAĞ TARAF: BİLGİLER VE YÜZ ---
    # Sağ tarafı da ikiye bölelim: Üstte Yüz, Altta Yazılar
    ax2 = fig.add_subplot(2, 2, 2)
    
    if result["face_found"] and result["face_image"]:
        ax2.imshow(result["face_image"])
        ax2.set_title("Tespit Edilen Kişi (Genişletilmiş)", color='green')
    else:
        ax2.text(0.5, 0.5, "YÜZ YOK", ha='center')
        ax2.set_title("Yüz Bulunamadı", color='red')
    ax2.axis('off')

    # Metin Alanı
    ax3 = fig.add_subplot(2, 2, 4)
    info_text = "--- ÇIKARILAN BİLGİLER ---\n\n"
    
    # Sırayla ve düzenli yaz
    keys_order = ["Isim_Soyisim", "Unvan", "Sirket", "ID_Sicil", "Email", "Konum", "Dogum_Tarihi", "Cinsiyet"]
    
    for key in keys_order:
        val = parsed.get(key)
        label = key.replace("_", " ")
        if val:
            info_text += f"• {label.ljust(15)}: {val}\n"
        else:
            info_text += f"• {label.ljust(15)}: ---\n"

    ax3.text(0.1, 0.9, info_text, fontsize=12, verticalalignment='top', family='monospace')
    ax3.axis('off')

    plt.tight_layout()
    return ax1 # Kartı çizmek için ekseni geri dön

def main():
    reader = SpatialCardReader()

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    print("\nLütfen kart görselini seçin...")
    file_path = filedialog.askopenfilename(filetypes=[("Resimler", "*.jpg *.png *.jpeg")])

    if not file_path: return

    # --- AYAR: YÜZ GENİŞLİĞİ ---
    # 0.5 = %50 daha geniş al demektir. İstersen artırabilirsin.
    result = reader.analyze_card(file_path, face_margin=0.5)

    if result["error"]:
        print(f"Hata: {result['error']}")
    else:
        # Sonuçları Görselleştir
        ax_card = visualize_complete_result(result)
        
        # Kart resmini sol tarafa koy
        img = Image.open(file_path)
        ax_card.imshow(img)
        
        # Konsola Bas
        print("\n--- SONUÇLAR ---")
        for k, v in result["parsed_data"].items():
            print(f"{k}: {v}")
            
        plt.show()

if __name__ == "__main__":
    main()