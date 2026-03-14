import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QFileDialog, QLabel, QProgressBar, 
                             QSlider, QFrame, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

class AltyaziUygulamasi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yapay Zeka Vizyon - Altyazi Duzenleyici")
        self.setMinimumSize(900, 600)
        
        #karanlık tema
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #333; margin-top: 10px; padding: 15px; border-radius: 8px; }
            QLabel { color: #e0e0e0; font-size: 13px; }
            QPushButton { background-color: #333; color: white; border-radius: 5px; padding: 8px; border: 1px solid #444; }
            QPushButton:hover { background-color: #444; }
            QPushButton#anaButon { background-color: #0078d4; border: none; font-weight: bold; height: 40px; }
            QPushButton#anaButon:hover { background-color: #1084d9; }
            QProgressBar { border: 1px solid #333; border-radius: 5px; text-align: center; color: white; background-color: #1e1e1e; }
            QProgressBar::chunk { background-color: #0078d4; }
            QSlider::handle:horizontal { background: #0078d4; border: 1px solid #0078d4; width: 18px; margin: -5px 0; border-radius: 9px; }
        """)
        
        self.arayuzu_hazirla()

    def arayuzu_hazirla(self):
        ana_yerlesim = QHBoxLayout() #sol panel 

        ayarlar_paneli = QVBoxLayout()
        
        #dosya secimi
        dosya_grubu = QGroupBox("1. Video Kaynagi")
        dosya_yerlesimi = QVBoxLayout()
        self.dosya_etiketi = QLabel("Dosya secilmedi...")
        dosya_sec_butonu = QPushButton(" Dosya Sec")
        dosya_sec_butonu.clicked.connect(self.dosya_ac)
        dosya_yerlesimi.addWidget(self.dosya_etiketi)
        dosya_yerlesimi.addWidget(dosya_sec_butonu)
        dosya_grubu.setLayout(dosya_yerlesimi)
        ayarlar_paneli.addWidget(dosya_grubu)

        # altyazi 
        stil_grubu = QGroupBox("2. Altyazi Gorunumu")
        stil_yerlesimi = QVBoxLayout()
        
        stil_yerlesimi.addWidget(QLabel("Arka Plan Saydamligi:"))
        self.saydamlik_kaydirici = QSlider(Qt.Orientation.Horizontal)
        self.saydamlik_kaydirici.setRange(0, 255)
        self.saydamlik_kaydirici.setValue(180)
        self.saydamlik_kaydirici.valueChanged.connect(self.onizlemeyi_guncelle)
        stil_yerlesimi.addWidget(self.saydamlik_kaydirici)

        #önizlme
        stil_yerlesimi.addWidget(QLabel("On Izleme:"))
        self.onizleme_cercevesi = QFrame()
        self.onizleme_cercevesi.setFixedSize(350, 150)
        self.onizleme_cercevesi.setStyleSheet("background-color: #2c3e50; border-radius: 5px;") 
        
        self.onizleme_yerlesimi = QVBoxLayout(self.onizleme_cercevesi)
        self.onizleme_metni = QLabel("Ornek Altyazi Metni (00:12)")
        self.onizleme_metni.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.onizleme_metni.setFixedWidth(250)
        self.onizlemeyi_guncelle() 
        
        self.onizleme_yerlesimi.addWidget(self.onizleme_metni, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        stil_yerlesimi.addWidget(self.onizleme_cercevesi)
        
        stil_grubu.setLayout(stil_yerlesimi)
        ayarlar_paneli.addWidget(stil_grubu)
        
        #sağ panel
        islem_paneli = QVBoxLayout()
        
        gunluk_grubu = QGroupBox("3. Islem Durumu ve Gunlukler")
        gunluk_yerlesimi = QVBoxLayout()
        self.ilerleme_cubugu = QProgressBar()
        self.gunluk_alani = QTextEdit()
        self.gunluk_alani.setReadOnly(True)
        self.gunluk_alani.setStyleSheet("background-color: #000; color: #00ff00; font-family: 'Consolas';")
        gunluk_yerlesimi.addWidget(self.ilerleme_cubugu)
        gunluk_yerlesimi.addWidget(self.gunluk_alani)
        gunluk_grubu.setLayout(gunluk_yerlesimi)
        
        islem_paneli.addWidget(gunluk_grubu)

        #baslat butonu
        self.baslat_butonu = QPushButton(" Islemi Baslat (Gomulu Altyazi)")
        self.baslat_butonu.setObjectName("anaButon")
        islem_paneli.addWidget(self.baslat_butonu)

        ana_yerlesim.addLayout(ayarlar_paneli, 1)
        ana_yerlesim.addLayout(islem_paneli, 2)

        ana_arac = QWidget()
        ana_arac.setLayout(ana_yerlesim)
        self.setCentralWidget(ana_arac)

    def onizlemeyi_guncelle(self):
        deger = self.saydamlik_kaydirici.value()
        self.onizleme_metni.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, {deger}); 
            color: white; 
            padding: 5px; 
            border-radius: 3px;
            font-size: 16px;
        """)

    def dosya_ac(self):
        dosya_adi, _ = QFileDialog.getOpenFileName(self, 'Video Sec', '', "Videolar (*.mp4 *.mkv *.avi)")
        if dosya_adi:
            temiz_isim = dosya_adi.split('/')[-1]
            self.dosya_etiketi.setText(f"Secilen: {temiz_isim}")

if __name__ == "__main__":
    uygulama = QApplication(sys.argv)
    pencere = AltyaziUygulamasi()
    pencere.show()
    sys.exit(uygulama.exec())