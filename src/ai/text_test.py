from text_moderator import TextModerator

def main():
    # Artık token göndermiyoruz, () içi boş kalabilir
    moderator = TextModerator()

    print("\n--- TEST BAŞLADI (Çıkış için 'q') ---")
    while True:
        txt = input("Metin: ")
        if txt == 'q': break
        
        sonuc = moderator.analyze_text(txt)
        
        if sonuc['is_toxic']:
            print(f"🚫 ENGEL: {sonuc['label']} (%{sonuc['score']})")
        else:
            print(f"✅ ONAY: {sonuc['label']} (%{sonuc['score']})")

if __name__ == "__main__":
    main()