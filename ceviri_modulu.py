import os
import torch
import datetime

# transformers 5.x ile 4.x arasindaki import yolu farkini otomatik handle et
try:
    from transformers import MarianMTModel, MarianTokenizer
except ImportError:
    try:
        from transformers.models.marian import MarianMTModel, MarianTokenizer
    except ImportError:
        raise ImportError(
            "MarianMTModel yuklenemedi.\n"
            "Terminalde su komutu calistirin:\n"
            "    pip install transformers==4.44.0 sentencepiece sacremoses safetensors"
        )

DOGRULANMIS_MODELLER = {
    ("en", "tr"): "Helsinki-NLP/opus-mt-tc-big-en-tr",
    ("tr", "en"): "Helsinki-NLP/opus-mt-tc-big-tr-en",
    ("de", "tr"): "Helsinki-NLP/opus-mt-de-tr",
    ("fr", "tr"): "Helsinki-NLP/opus-mt-fr-tr",
    ("es", "tr"): "Helsinki-NLP/opus-mt-es-tr",
    ("ru", "tr"): "Helsinki-NLP/opus-mt-ru-tr",
    ("ar", "tr"): "Helsinki-NLP/opus-mt-ar-tr",
    ("tr", "de"): "Helsinki-NLP/opus-mt-tr-de",
    ("tr", "fr"): "Helsinki-NLP/opus-mt-tr-fr",
}

def model_adi_bul(kaynak_dil, hedef_dil):
    anahtar = (kaynak_dil, hedef_dil)
    if anahtar in DOGRULANMIS_MODELLER:
        return DOGRULANMIS_MODELLER[anahtar]
    return "Helsinki-NLP/opus-mt-" + kaynak_dil + "-" + hedef_dil


def _torch_load_patch():
    _orijinal = torch.load
    def _patched(*args, **kwargs):
        if "weights_only" not in kwargs:
            kwargs["weights_only"] = False
        return _orijinal(*args, **kwargs)
    torch.load = _patched
    return _orijinal


class CeviriVeSrtYoneticisi:
    def __init__(self, kaynak_dil="en", hedef_dil="tr", yerel_model_dizini=None):
        self.kaynak_dil = kaynak_dil
        self.hedef_dil = hedef_dil
        self.kelime_ayirici = None
        self.ceviri_modeli = None

        if yerel_model_dizini:
            model_adi = os.path.basename(model_adi_bul(kaynak_dil, hedef_dil))
            self.model_yolu = os.path.join(yerel_model_dizini, model_adi)
        else:
            self.model_yolu = model_adi_bul(kaynak_dil, hedef_dil)

        print("[" + kaynak_dil + " -> " + hedef_dil + "] model yukleniyor: " + self.model_yolu)

        if torch.cuda.is_available():
            self.cihaz = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.cihaz = torch.device("mps")
        else:
            self.cihaz = torch.device("cpu")

        print("Donanim: " + str(self.cihaz))
        self._modeli_yukle()

    def _modeli_yukle(self):
        son_hata = None

        # DENEME 1: safetensors
        try:
            print("Deneme 1/3: safetensors...")
            self.kelime_ayirici = MarianTokenizer.from_pretrained(self.model_yolu)
            self.ceviri_modeli = MarianMTModel.from_pretrained(
                self.model_yolu, use_safetensors=True
            ).to(self.cihaz)
            print("Model safetensors ile yuklendi.")
            return
        except Exception as e:
            son_hata = e
            print("  safetensors basarisiz: " + str(e)[:120])

        # DENEME 2: .bin + torch patch
        orijinal = None
        try:
            print("Deneme 2/3: .bin + torch patch...")
            orijinal = _torch_load_patch()
            if self.kelime_ayirici is None:
                self.kelime_ayirici = MarianTokenizer.from_pretrained(self.model_yolu)
            self.ceviri_modeli = MarianMTModel.from_pretrained(
                self.model_yolu, use_safetensors=False
            ).to(self.cihaz)
            print("Model .bin ile yuklendi.")
            return
        except Exception as e:
            son_hata = e
            print("  .bin basarisiz: " + str(e)[:120])
        finally:
            if orijinal is not None:
                torch.load = orijinal

        # DENEME 3: standart
        try:
            print("Deneme 3/3: standart yukleme...")
            if self.kelime_ayirici is None:
                self.kelime_ayirici = MarianTokenizer.from_pretrained(self.model_yolu)
            self.ceviri_modeli = MarianMTModel.from_pretrained(self.model_yolu).to(self.cihaz)
            print("Model standart yontemle yuklendi.")
            return
        except Exception as e:
            son_hata = e
            print("  standart basarisiz: " + str(e)[:120])

        self.kelime_ayirici = None
        self.ceviri_modeli = None
        hata_str = str(son_hata)

        if "v2.6" in hata_str or "weights_only" in hata_str:
            cozum = (
                "PyTorch surum kisitlamasi.\n"
                "Terminalde su komutu calistirin:\n\n"
                "    pip install --upgrade transformers safetensors"
            )
        elif "not a valid model" in hata_str or "404" in hata_str:
            cozum = (
                "Model bulunamadi: " + self.model_yolu + "\n"
                "'" + self.kaynak_dil + "->" + self.hedef_dil + "' desteklenmiyor olabilir."
            )
        else:
            cozum = (
                "Terminalde su komutu calistirin:\n\n"
                "    pip install --upgrade transformers safetensors sentencepiece sacremoses"
            )

        raise Exception("Ceviri modeli yuklenemedi!\n\n" + cozum + "\n\nDetay: " + hata_str)

    def _hazir_mi(self):
        if self.kelime_ayirici is None or self.ceviri_modeli is None:
            raise RuntimeError("Ceviri modeli yuklenmemis.")

    def metinleri_toplu_cevir(self, metinler, yigin_boyutu=16, ilerleme_kancasi=None):
        self._hazir_mi()
        if not metinler:
            return []

        cevrilmis_metinler = []
        toplam_metin = len(metinler)

        for i in range(0, toplam_metin, yigin_boyutu):
            yigin = metinler[i:i + yigin_boyutu]
            girdi_verisi = self.kelime_ayirici(
                yigin, return_tensors="pt", padding=True, truncation=True
            ).to(self.cihaz)

            with torch.no_grad():
                cevrilmis_cikti = self.ceviri_modeli.generate(**girdi_verisi)

            cevrilmis_yigin = self.kelime_ayirici.batch_decode(
                cevrilmis_cikti, skip_special_tokens=True
            )
            cevrilmis_metinler.extend(cevrilmis_yigin)

            if ilerleme_kancasi:
                islenen = min(i + yigin_boyutu, toplam_metin)
                yuzde = int((islenen / toplam_metin) * 100)
                ilerleme_kancasi(yuzde)

        return cevrilmis_metinler

    def saniyeyi_zaman_damgasina_cevir(self, saniye):
        zaman_farki = datetime.timedelta(seconds=saniye)
        toplam_saniye = int(zaman_farki.total_seconds())
        saat = toplam_saniye // 3600
        dakika = (toplam_saniye % 3600) // 60
        kalan_saniye = toplam_saniye % 60
        milisaniye = int(zaman_farki.microseconds / 1000)
        return "%02d:%02d:%02d,%03d" % (saat, dakika, kalan_saniye, milisaniye)

    def altyazi_olustur(self, ses_verileri, dosya_adi, ilerleme_kancasi=None):
        self._hazir_mi()
        if not ses_verileri:
            return dosya_adi

        orijinal_metinler = [veri['metin'] for veri in ses_verileri]
        cevrilmis_metinler = self.metinleri_toplu_cevir(
            orijinal_metinler, yigin_boyutu=16, ilerleme_kancasi=ilerleme_kancasi
        )

        with open(dosya_adi, "w", encoding="utf-8") as dosya:
            for indeks, (veri, ceviri) in enumerate(zip(ses_verileri, cevrilmis_metinler), start=1):
                baslangic = self.saniyeyi_zaman_damgasina_cevir(veri['baslangic'])
                bitis = self.saniyeyi_zaman_damgasina_cevir(veri['bitis'])
                dosya.write(str(indeks) + "\n")
                dosya.write(baslangic + " --> " + bitis + "\n")
                dosya.write(ceviri + "\n\n")

        return dosya_adi