from transformers import MarianMTModel, MarianTokenizer

class CeviriYoneticisi:
    def __init__(self, kaynak_dil="en", hedef_dil="tr"):
        self.model_adi = f"Helsinki-NLP/opus-mt-tc-big-{kaynak_dil}-{hedef_dil}"
        self.kelime_ayirici = MarianTokenizer.from_pretrained(self.model_adi)
        self.ceviri_modeli = MarianMTModel.from_pretrained(self.model_adi)

    def metni_cevir(self, kaynak_metin):
        girdi_verisi = self.kelime_ayirici(kaynak_metin, return_tensors="pt", padding=True)
        cevrilmis_ciktilar = self.ceviri_modeli.generate(**girdi_verisi)
        tamamlanmis_ceviri = [self.kelime_ayirici.decode(c, skip_special_tokens=True) for c in cevrilmis_ciktilar]
        return tamamlanmis_ceviri[0]

if __name__ == "__main__":
    ceviri_araci = CeviriYoneticisi()
    ornek_metin = "The system works completely offline for data privacy."
    ornek_sonuc = ceviri_araci.metni_cevir(ornek_metin)
    print(ornek_sonuc)