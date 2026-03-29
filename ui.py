import sys
import os
import cv2  # Videoyu okumak ve kare yakalamak icin
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QFileDialog, QLabel, QProgressBar, 
                             QSlider, QFrame, QTextEdit, QGroupBox, QComboBox, QListWidget,
                             QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap, QFont

# 1. Islem Yonetimi (Arka plan calisani)
class AltyaziIsleyicisi(QThread):
    ilerleme = pyqtSignal(int, str)
    tamamlandi = pyqtSignal(bool)

    def run(self):
        adimlar = [
            (20, "Ses Ayristiriliyor (FFmpeg)..."),
            (50, "Metne Donusturuluyor (Whisper)..."),
            (80, "Ceviri Yapiliyor (Helsinki-NLP)..."),
            (100, "Videonun Uzerine Isleniyor (Hardsubbing)...")
        ]
        for p, mesaj in adimlar:
            self.ilerleme.emit(p, mesaj)
            self.msleep(1500) 
        self.tamamlandi.emit(True)

# 2. Ana Uygulama Penceresi
class ModernAltyaziUygulamasi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Vision - Profesyonel Altyazi Duzenleyici")
        self.setMinimumSize(1100, 750)
        self.setAcceptDrops(True) 
        self.dosya_yolu = ""
        self.cikti_yolu = ""
        
        self.stilleri_uygula()
        self.arayuzu_hazirla()

    def stilleri_uygula(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0f111a; }
            QGroupBox { color: #82aaff; font-weight: bold; border: 1px solid #1f2233; margin-top: 15px; padding: 10px; border-radius: 5px; }
            QLabel { color: #bfc7d5; }
            QPushButton { background-color: #1f2233; color: #eeffff; border-radius: 4px; padding: 8px; }
            QPushButton:hover { background-color: #292d3e; }
            #suruklemeAlani { border: 2px dashed #444; border-radius: 10px; background-color: #1a1c25; }
            #islemButonu { background-color: #c3e88d; color: #000; font-weight: bold; }
            #iptalButonu { background-color: #ff5370; color: #fff; }
        """)

    def arayuzu_hazirla(self):
        ana_yerlesim = QHBoxLayout()
        sol_panel = QVBoxLayout()

        # --- SOL TARAF: AYARLAR ---
        self.surukleme_etiketi = QLabel("\n\n🎥 Videoyu Buraya Surukle\n(MP4, MKV, AVI)")
        self.surukleme_etiketi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.surukleme_etiketi.setObjectName("suruklemeAlani")
        self.surukleme_etiketi.setFixedSize(350, 150)
        sol_panel.addWidget(self.surukleme_etiketi)

        bilgi_grubu = QGroupBox("Dosya Bilgisi")
        self.bilgi_etiketi = QLabel("Cozunurluk: -\nSure: -\nFormat: -")
        bilgi_yerlesimi = QVBoxLayout()
        bilgi_yerlesimi.addWidget(self.bilgi_etiketi)
        bilgi_grubu.setLayout(bilgi_yerlesimi)
        sol_panel.addWidget(bilgi_grubu)

        # Altyazi Stili
        stil_grubu = QGroupBox("Altyazi Stili")
        stil_yerlesimi = QVBoxLayout()
        
        h_yerlesim = QHBoxLayout()
        self.font_kutusu = QComboBox()
        self.font_kutusu.addItems(["Arial", "Verdana", "Times New Roman", "Courier New"])
        self.font_kutusu.currentTextChanged.connect(self.altyazi_onizlemesini_guncelle)
        
        self.font_boyutu = QSpinBox()
        self.font_boyutu.setRange(10, 80)
        self.font_boyutu.setValue(24)
        self.font_boyutu.valueChanged.connect(self.altyazi_onizlemesini_guncelle)
        
        h_yerlesim.addWidget(QLabel("Font:"))
        h_yerlesim.addWidget(self.font_kutusu)
        h_yerlesim.addWidget(QLabel("Boyut:"))
        h_yerlesim.addWidget(self.font_boyutu)
        stil_yerlesimi.addLayout(h_yerlesim)

        stil_yerlesimi.addWidget(QLabel("Konum:"))
        self.konum_kutusu = QComboBox()
        self.konum_kutusu.addItems(["Alt (Bottom)", "Orta (Middle)", "Ust (Top)"])
        self.konum_kutusu.currentIndexChanged.connect(self.altyazi_onizlemesini_guncelle)
        stil_yerlesimi.addWidget(self.konum_kutusu)

        stil_yerlesimi.addWidget(QLabel("Saydamlik:"))
        self.saydamlik_kaydirici = QSlider(Qt.Orientation.Horizontal)
        self.saydamlik_kaydirici.setRange(0, 255)
        self.saydamlik_kaydirici.setValue(180)
        self.saydamlik_kaydirici.valueChanged.connect(self.altyazi_onizlemesini_guncelle)
        stil_yerlesimi.addWidget(self.saydamlik_kaydirici)
        
        stil_grubu.setLayout(stil_yerlesimi)
        sol_panel.addWidget(stil_grubu)

        self.cikti_butonu = QPushButton("📂 Cikti Klasoru Sec")
        self.cikti_butonu.clicked.connect(self.cikti_klasoru_sec)
        sol_panel.addWidget(self.cikti_butonu)

        # --- SAG TARAF: CANLI VIDEO ON IZLEME ---
        sag_panel = QVBoxLayout()

        self.onizleme_kapsayici = QWidget()
        self.onizleme_kapsayici.setFixedSize(640, 360)
        self.onizleme_kapsayici.setStyleSheet("background-color: #000; border: 1px solid #333;")
        
        self.video_karesi = QLabel(self.onizleme_kapsayici)
        self.video_karesi.setFixedSize(640, 360)
        self.video_karesi.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Dinamik Altyazi Katmani
        self.katman_yerlesimi = QVBoxLayout(self.onizleme_kapsayici)
        self.altyazi_katmani = QLabel("Altyazilar Boyle Gozukur")
        self.altyazi_katmani.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.altyazi_katmani.setHidden(True)
        self.katman_yerlesimi.addWidget(self.altyazi_katmani)

        sag_panel.addWidget(QLabel("Canli On Izleme Paneli:"))
        sag_panel.addWidget(self.onizleme_kapsayici)

        self.altyazi_listesi = QListWidget()
        self.altyazi_listesi.setMaximumHeight(150)
        sag_panel.addWidget(QLabel("Zaman Damgali Metinler (Onizleme):"))
        sag_panel.addWidget(self.altyazi_listesi)

        dil_yerlesimi = QHBoxLayout()
        self.dil_kutusu = QComboBox()
        self.dil_kutusu.addItems(["Turkce (Helsinki-NLP)", "Ingilizce", "Almanca"])
        dil_yerlesimi.addWidget(QLabel("Hedef Dil Secimi:"))
        dil_yerlesimi.addWidget(self.dil_kutusu)
        sag_panel.addLayout(dil_yerlesimi)

        self.ilerleme_cubugu = QProgressBar()
        self.durum_mesaji = QLabel("Hazir")
        sag_panel.addWidget(self.durum_mesaji)
        sag_panel.addWidget(self.ilerleme_cubugu)

        butonlar = QHBoxLayout()
        self.baslat_butonu = QPushButton("Islemi Baslat")
        self.baslat_butonu.setObjectName("islemButonu")
        self.baslat_butonu.clicked.connect(self.islemi_baslat)
        self.iptal_butonu = QPushButton("Iptal")
        self.iptal_butonu.setObjectName("iptalButonu")
        self.iptal_butonu.setEnabled(False)
        self.iptal_butonu.clicked.connect(self.islemi_iptal_et)
        butonlar.addWidget(self.baslat_butonu)
        butonlar.addWidget(self.iptal_butonu)
        sag_panel.addLayout(butonlar)

        ana_yerlesim.addLayout(sol_panel, 1)
        ana_yerlesim.addLayout(sag_panel, 2)
        kapsayici = QWidget()
        kapsayici.setLayout(ana_yerlesim)
        self.setCentralWidget(kapsayici)

    # --- ON IZLEME MANTIK GUNCELLEMELERI ---
    def katman_yerlesimini_temizle(self):
        """Yerlesim icindeki bosluklari ve elemanlari temizler."""
        while self.katman_yerlesimi.count():
            item = self.katman_yerlesimi.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def altyazi_onizlemesini_guncelle(self):
        """Altyazi ayarlarini canli olarak hem yaziya hem konuma uygular."""
        if not self.dosya_yolu: return

        font_ailesi = self.font_kutusu.currentText()
        boyut = self.font_boyutu.value()
        saydamlik = self.saydamlik_kaydirici.value()
        konum_indeksi = self.konum_kutusu.currentIndex()

        # Yerlesimi sifirla
        self.katman_yerlesimini_temizle()

        # Konumu ayarla (Bosluk/Stretch mantigi)
        if konum_indeksi == 0: # Alt
            self.katman_yerlesimi.addStretch()
            self.katman_yerlesimi.addWidget(self.altyazi_katmani)
        elif konum_indeksi == 1: # Orta
            self.katman_yerlesimi.addStretch()
            self.katman_yerlesimi.addWidget(self.altyazi_katmani)
            self.katman_yerlesimi.addStretch()
        else: # Ust
            self.katman_yerlesimi.addWidget(self.altyazi_katmani)
            self.katman_yerlesimi.addStretch()

        # Stili uygula
        self.altyazi_katmani.setStyleSheet(f"""
            color: rgba(255, 255, 255, {saydamlik});
            font-family: {font_ailesi};
            font-size: {boyut}px;
            background-color: rgba(0, 0, 0, {saydamlik});
            padding: 10px;
            border-radius: 5px;
        """)
        self.altyazi_katmani.setHidden(False)

    def video_onizlemesini_goster(self, yol):
        yakala = cv2.VideoCapture(yol)
        genislik = int(yakala.get(cv2.CAP_PROP_FRAME_WIDTH))
        yukseklik = int(yakala.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.bilgi_etiketi.setText(f"Cozunurluk: {genislik}x{yukseklik}\nFormat: {os.path.splitext(yol)[1].upper()[1:]}")

        basarili, kare = yakala.read()
        if basarili:
            kare = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            h, w, ch = kare.shape
            q_resim = QImage(kare.data, w, h, ch * w, QImage.Format.Format_RGB888)
            piksel_haritasi = QPixmap.fromImage(q_resim)
            self.video_karesi.setPixmap(piksel_haritasi.scaled(640, 360, Qt.AspectRatioMode.KeepAspectRatio))
            self.altyazi_onizlemesini_guncelle()
        yakala.release()

    def dragEnterEvent(self, olay: QDragEnterEvent):
        if olay.mimeData().hasUrls(): olay.accept()
        else: olay.ignore()

    def dropEvent(self, olay: QDropEvent):
        dosyalar = [u.toLocalFile() for u in olay.mimeData().urls()]
        if dosyalar:
            self.dosya_yolu = dosyalar[0]
            if os.path.splitext(self.dosya_yolu)[1].lower() in ['.mp4', '.mkv', '.avi']:
                self.surukleme_etiketi.setText(f"Dosya: {os.path.basename(self.dosya_yolu)}")
                self.altyazi_listesi.clear()
                self.video_onizlemesini_goster(self.dosya_yolu)
            else:
                QMessageBox.warning(self, "Hata", "Gecersiz format!")

    def cikti_klasoru_sec(self):
        self.cikti_yolu = QFileDialog.getExistingDirectory(self, "Klasor Sec")

    def islemi_baslat(self):
        if not self.dosya_yolu: return
        self.isleyici = AltyaziIsleyicisi()
        self.isleyici.ilerleme.connect(self.arayuzu_guncelle)
        self.isleyici.tamamlandi.connect(self.islem_tamamlandi)
        self.isleyici.start()
        self.baslat_butonu.setEnabled(False)
        self.iptal_butonu.setEnabled(True)

    def arayuzu_guncelle(self, deger, mesaj):
        self.ilerleme_cubugu.setValue(deger)
        self.durum_mesaji.setText(mesaj)

    def islemi_iptal_et(self):
        if hasattr(self, 'isleyici'): self.isleyici.terminate()
        self.baslat_butonu.setEnabled(True)
        self.durum_mesaji.setText("Islem iptal edildi.")

    def islem_tamamlandi(self):
        self.baslat_butonu.setEnabled(True)
        self.iptal_butonu.setEnabled(False)
        QMessageBox.information(self, "Basarili", "Islem basariyla tamamlandi!")

if __name__ == "__main__":
    uygulama = QApplication(sys.argv)
    pencere = ModernAltyaziUygulamasi()
    pencere.show()
    sys.exit(uygulama.exec())