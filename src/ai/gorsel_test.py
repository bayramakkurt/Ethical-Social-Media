import tkinter as tk
from tkinter import filedialog
from content_moderator import ContentModerator # 1. Dosyayı import ediyoruz

def main():
    # 1. Modeli Başlat (Sadece bir kere çalışır, nesne oluşur)
    # Bu nesneyi global olarak tutup her istekte tekrar tekrar kullanmalısın.
    moderator = ContentModerator()

    # --- Test için dosya seçimi ---
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    print("\nLütfen analiz edilecek resmi seçin...")
    file_path = filedialog.askopenfilename(
        title="Resim Seç",
        filetypes=[("Resimler", "*.jpg *.jpeg *.png *.webp")]
    )

    if not file_path:
        print("İşlem iptal edildi.")
        return

    # 2. FONKSİYONU ÇAĞIRMA (İstediğin Kısım)
    # Tek satırda sonucu alıyoruz
    result = moderator.analyze_image(file_path)

    # 3. Sonuçları Kullanma
    print("\n" + "="*30)
    print(f"SONUÇ RAPORU")
    print("="*30)
    print(f"Tespit Edilen : {result['label']}")
    print(f"Güven Skoru   : %{result['score']}")
    print(f"Durum         : {'✅ ONAYLANDI' if result['is_shareable'] else '❌ REDDEDİLDİ'}")
    print("="*30)

    # Örnek: Eğer reddedilirse ne yapılacak?
    if result['is_shareable']:
        print("-> Veritabanına kaydediliyor...")
    else:
        print("-> Kullanıcıya uyarı mesajı gönderiliyor: 'Görseliniz topluluk kurallarına uymuyor.'")

if __name__ == "__main__":
    main()