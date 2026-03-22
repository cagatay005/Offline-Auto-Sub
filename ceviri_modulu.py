import datetime
from transformers import MarianMTModel, MarianTokenizer

class CeviriVeSrtYoneticisi:
    def __init__(self, kaynak_dil="en", hedef_dil="tr", yerel_model_dizini=None):
        """
        Dinamik dil seçimi ve çevrimdışı model yükleme desteği eklendi.
        """
        self.kaynak_dil = kaynak_dil
        self.hedef_dil = hedef_dil
        
        # Projenin çevrimdışı çalışma gereksinimi için yerel dizin kontrolü
        if yerel_model_dizini:
            self.model_yolu = f"{yerel_model_dizini}/opus-mt-{self.kaynak_dil}-{self.hedef_dil}"
        else:
            # Yerel dizin yoksa Hugging Face üzerinden varsayılan model adını oluştur
            self.model_yolu = f"Helsinki-NLP/opus-mt-{self.kaynak_dil}-{self.hedef_dil}"

        print(f"[{self.kaynak_dil} -> {self.hedef_dil}] yönü için model yükleniyor: {self.model_yolu}")
        
        try:
            self.kelime_ayirici = MarianTokenizer.from_pretrained(self.model_yolu)
            self.ceviri_modeli = MarianMTModel.from_pretrained(self.model_yolu)
            print("Çeviri modeli başarıyla hazırlandı.")
        except Exception as hata:
            print(f"Model yüklenirken kritik hata! Lütfen dil kodlarını veya yerel model dosyalarını kontrol edin.\nHata Detayı: {hata}")

    def metinleri_cevir(self, metin_listesi):
        # Boş liste kontrolü eklendi (Sistem kararlılığı için)
        if not metin_listesi:
            return []
            
        girdi_verisi = self.kelime_ayirici(metin_listesi, return_tensors="pt", padding=True, truncation=True)
        cevrilmis_ciktilar = self.ceviri_modeli.generate(**girdi_verisi)
        return [self.kelime_ayirici.decode(c, skip_special_tokens=True) for c in cevrilmis_ciktilar]

    def saniyeyi_zaman_damgasina_cevir(self, saniye):
        zaman_farki = datetime.timedelta(seconds=saniye)
        toplam_saniye = int(zaman_farki.total_seconds())
        saat = toplam_saniye // 3600
        dakika = (toplam_saniye % 3600) // 60
        kalan_saniye = toplam_saniye % 60
        milisaniye = int(zaman_farki.microseconds / 1000)
        return f"{saat:02d}:{dakika:02d}:{kalan_saniye:02d},{milisaniye:03d}"

    def altyazi_dosyasi_olustur(self, ses_verileri, dosya_adi):
        kaynak_metinler = [veri['metin'] for veri in ses_verileri]
        cevrilmis_metinler = self.metinleri_cevir(kaynak_metinler)
        
        with open(dosya_adi, "w", encoding="utf-8") as dosya:
            for indeks, (orijinal, ceviri) in enumerate(zip(ses_verileri, cevrilmis_metinler), start=1):
                baslangic = self.saniyeyi_zaman_damgasina_cevir(orijinal['baslangic'])
                bitis = self.saniyeyi_zaman_damgasina_cevir(orijinal['bitis'])
                
                dosya.write(f"{indeks}\n")
                dosya.write(f"{baslangic} --> {bitis}\n")
                dosya.write(f"{ceviri}\n\n")

if __name__ == "__main__":
    # Test için İspanyolca'dan Türkçe'ye çevrimdışı model dizini simülasyonu
    # yonetici = CeviriVeSrtYoneticisi(kaynak_dil="es", hedef_dil="tr", yerel_model_dizini="./modeller")
    
    yonetici = CeviriVeSrtYoneticisi(kaynak_dil="en", hedef_dil="tr")
    
    ornek_ses_verileri = [
        {'baslangic': 0.0, 'bitis': 3.5, 'metin': 'The system works completely offline for data privacy.'},
        {'baslangic': 4.0, 'bitis': 7.2, 'metin': 'We do not need any external API connection.'}
    ]
    
    yonetici.altyazi_dosyasi_olustur(ornek_ses_verileri, "proje_ciktisi.srt")