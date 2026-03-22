import subprocess
import whisper
import os

def sesi_ayristir(video_yolu, cikti_ses_yolu="gecici_ses.wav"):
    komut = [
        "ffmpeg", "-y", "-i", video_yolu, 
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", cikti_ses_yolu
    ]
    subprocess.run(komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return cikti_ses_yolu

def videodan_metin_cikar(orijinal_video, model_boyutu="medium"):    #Whisper medium model kullanıldı
    gecici_ses = "gecici_ses.wav"

    try:
        sesi_ayristir(orijinal_video, gecici_ses)       #videodan sesi ayıkladıktan sonra geçici bir dosyaya kaydedildi
        
        model = whisper.load_model(model_boyutu)
        sonuc = model.transcribe(gecici_ses, fp16=False)    #sesi metne dönüştürme
        
        return {
            "dil": sonuc.get("language", "Bilinmiyor"),
            "tam_metin": sonuc["text"], 
            "segmentler": sonuc["segments"]         # SRT oluşturmak için zaman damgalı segmentler eklendi
        }

    finally:
        if os.path.exists(gecici_ses):
            os.remove(gecici_ses)           # Geçici ses dosyasını yer kaplamaması için sildirdik

if __name__ == "__main__":
    test_video = "test.mp4" 
    
    if os.path.exists(test_video):
        stt_verisi = videodan_metin_cikar(test_video)
        
        if stt_verisi:
            print("\n--- TEST SONUÇLARI ---")
            print(f"Tespit Edilen Dil: {stt_verisi['dil'].upper()}")
            
            print("\n--- Videonun Tam Metni ---")
            print(stt_verisi['tam_metin'])
            
            print(f"\n--- SRT İçin Çıkarılan Segment Sayısı: {len(stt_verisi['segmentler'])} ---")
            if len(stt_verisi['segmentler']) > 0:
                print("Örnek İlk Segment Verisi:")
                print(stt_verisi['segmentler'][0])          # NLP modülüne gidecek zaman damgalı verinin örneği
        else:
            print("Video bulunamadi.")