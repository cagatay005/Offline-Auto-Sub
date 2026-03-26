import datetime
import threading
from transformers import MarianMTModel, MarianTokenizer

class CeviriVeSrtYoneticisi:
    def __init__(self, kaynak_dil="en", hedef_dil="tr", yerel_model_dizini=None):
        self.kaynak_dil = kaynak_dil
        self.hedef_dil = hedef_dil
        
        if yerel_model_dizini:
            self.model_yolu = f"{yerel_model_dizini}/opus-mt-{self.kaynak_dil}-{self.hedef_dil}"
        else:
            self.model_yolu = f"Helsinki-NLP/opus-mt-{self.kaynak_dil}-{self.hedef_dil}"

        print(f"[{self.kaynak_dil} -> {self.hedef_dil}] yönü için model yükleniyor: {self.model_yolu}")
        
        try:
            self.kelime_ayirici = MarianTokenizer.from_pretrained(self.model_yolu)
            self.ceviri_modeli = MarianMTModel.from_pretrained(self.model_yolu)
            print("Çeviri modeli başarıyla hazırlandı.")
        except Exception as hata:
            print(f"Model yüklenirken kritik hata! Hata Detayı: {hata}")

    def metni_cevir(self, metin):
        """Tekil metin çevirisi yapar (İlerleme çubuğunu doğru hesaplamak için)."""
        if not metin:
            return ""
        girdi_verisi = self.kelime_ayirici([metin], return_tensors="pt", padding=True, truncation=True)
        cevrilmis_cikti = self.ceviri_modeli.generate(**girdi_verisi)
        return self.kelime_ayirici.decode(cevrilmis_cikti[0], skip_special_tokens=True)

    def saniyeyi_zaman_damgasina_cevir(self, saniye):
        zaman_farki = datetime.timedelta(seconds=saniye)
        toplam_saniye = int(zaman_farki.total_seconds())
        saat = toplam_saniye // 3600
        dakika = (toplam_saniye % 3600) // 60
        kalan_saniye = toplam_saniye % 60
        milisaniye = int(zaman_farki.microseconds / 1000)
        return f"{saat:02d}:{dakika:02d}:{kalan_saniye:02d},{milisaniye:03d}"

    def _islem_dongusu(self, ses_verileri, dosya_adi, ilerleme_kancasi, bitis_kancasi):
        """Thread fonksiyonu."""
        toplam_parca = len(ses_verileri)
        
        # Dosyayı anında yazma modülü (daha tasarruflu RAM kullanımı için)
        with open(dosya_adi, "w", encoding="utf-8") as dosya:
            for indeks, veri in enumerate(ses_verileri, start=1):
                # 1. metni cevir
                ceviri = self.metni_cevir(veri['metin'])
                
                # 2. zaman damgalarını hesapla
                baslangic = self.saniyeyi_zaman_damgasina_cevir(veri['baslangic'])
                bitis = self.saniyeyi_zaman_damgasina_cevir(veri['bitis'])
                
                # 3. srt ye anında yaz
                dosya.write(f"{indeks}\n")
                dosya.write(f"{baslangic} --> {bitis}\n")
                dosya.write(f"{ceviri}\n\n")
                
                # 4. GUI'ye ilerleme Durumunu bildir
                if ilerleme_kancasi:
                    yuzde = int((indeks / toplam_parca) * 100)
                    ilerleme_kancasi(yuzde)
        
        # Tüm işlem bittiğinde GUI'ye haber ver
        if bitis_kancasi:
            bitis_kancasi(dosya_adi)

    def altyazi_olustur_arka_planda(self, ses_verileri, dosya_adi, ilerleme_kancasi=None, bitis_kancasi=None):
        """
        GUI'nin donmasını engelleyen, multithreading destekli ana fonksiyon.
        """
        # İşlemi ana programdan koparıp arka plana alma
        is_parcacigi = threading.Thread(
            target=self._islem_dongusu,
            args=(ses_verileri, dosya_adi, ilerleme_kancasi, bitis_kancasi),
            daemon=True
        )
        is_parcacigi.start()
        return is_parcacigi


if __name__ == "__main__":
    import time

    yonetici = CeviriVeSrtYoneticisi(kaynak_dil="en", hedef_dil="tr")
    
    ornek_ses_verileri = [
        {'baslangic': 0.0, 'bitis': 3.5, 'metin': 'The system works completely offline for data privacy.'},
        {'baslangic': 4.0, 'bitis': 7.2, 'metin': 'We do not need any external API connection.'},
        {'baslangic': 8.0, 'bitis': 10.5, 'metin': 'Multithreading prevents the GUI from freezing.'}
    ]
    
    # --- Arayüz simülasyonu ---
    def arayuzu_guncelle(yuzde):
        print(f"İlerleme: %{yuzde} tamamlandı...")

    def islem_tamamlandi(dosya_yolu):
        print(f"İşlem bitti! Altyazı hazır: {dosya_yolu}")

    print("Arka planda çeviri başlatılıyor...")
    
    yonetici.altyazi_olustur_arka_planda(
        ses_verileri=ornek_ses_verileri, 
        dosya_adi="proje_ciktisi.srt",
        ilerleme_kancasi=arayuzu_guncelle,
        bitis_kancasi=islem_tamamlandi
    )
    
    # Bu döngü, arka plandaki işlem bitene kadar ana programın kapanmasını engeller
    while threading.active_count() > 1:
        time.sleep(0.5)