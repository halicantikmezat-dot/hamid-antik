import sys
import requests
import webbrowser
from urllib.parse import quote
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QTextEdit, QGroupBox, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

class MezatAdminPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_url = "https://reenact-doorknob-voucher.ngrok-free.dev"
        self.current_price = 0
        self.last_bidder = "-"
        self.bid_history = []
        self.countdown_val = 3
        
        self.initUI()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.get_status)
        self.timer.start(1000)

        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)

    def initUI(self):
        self.setWindowTitle("Hamdullah Mezat - Canlı Mezat Yönetim Paneli")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #1e1e2e; color: #ffffff;")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        left_layout = QVBoxLayout()

        conn_box = QGroupBox("Sunucu Bağlantısı")
        conn_box.setStyleSheet("color: #a6adc8; font-weight: bold;")
        conn_layout = QHBoxLayout()
        self.url_input = QLineEdit(self.server_url)
        self.url_input.setStyleSheet("background-color: #313244; color: #ffffff; padding: 6px; border-radius: 4px;")
        btn_connect = QPushButton("Yeniden Bağlan")
        btn_connect.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 6px;")
        btn_connect.clicked.connect(self.update_server_url)
        conn_layout.addWidget(self.url_input)
        conn_layout.addWidget(btn_connect)
        conn_box.setLayout(conn_layout)
        left_layout.addWidget(conn_box)

        info_box = QGroupBox("Canlı Mezat Durumu")
        info_box.setStyleSheet("color: #a6adc8; font-weight: bold;")
        info_layout = QVBoxLayout()

        self.lbl_product = QLabel("📦 Ürün: Yükleniyor...")
        self.lbl_product.setFont(QFont("Arial", 16, QFont.Bold))
        self.lbl_product.setStyleSheet("color: #f9e2af;")

        self.lbl_price = QLabel("0.00 ₺")
        self.lbl_price.setFont(QFont("Arial", 36, QFont.Bold))
        self.lbl_price.setStyleSheet("color: #a6e3a1;")

        self.lbl_bidder = QLabel("Son Pey Veren: -")
        self.lbl_bidder.setFont(QFont("Arial", 14))

        self.lbl_status = QLabel("DURUM: AKTİF")
        self.lbl_status.setFont(QFont("Arial", 18, QFont.Bold))
        self.lbl_status.setStyleSheet("color: #89b4fa;")

        info_layout.addWidget(self.lbl_product)
        info_layout.addWidget(self.lbl_price)
        info_layout.addWidget(self.lbl_bidder)
        info_layout.addWidget(self.lbl_status)
        info_box.setLayout(info_layout)
        left_layout.addWidget(info_box)

        ctrl_box = QGroupBox("Hızlı Pey & Satış Kontrolleri")
        ctrl_box.setStyleSheet("color: #a6adc8; font-weight: bold;")
        ctrl_layout = QVBoxLayout()

        self.input_bidder = QLineEdit()
        self.input_bidder.setPlaceholderText("Müşteri Adı / Rumuz")
        self.input_bidder.setStyleSheet("background-color: #313244; color: #ffffff; padding: 8px; border-radius: 4px;")

        btn_bid = QPushButton("⚡ Manuel Pey Ekle (+50 ₺) [Boşluk Tuşu]")
        btn_bid.setStyleSheet("background-color: #fab387; color: #11111b; font-weight: bold; padding: 10px; font-size: 14px;")
        btn_bid.clicked.connect(self.add_manual_bid)

        btn_undo = QPushButton("↩️ Son Peyi Geri Al / İptal Et")
        btn_undo.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 8px;")
        btn_undo.clicked.connect(self.undo_bid)

        btn_countdown = QPushButton("⏱️ 3-2-1 Geri Sayım Başlat")
        btn_countdown.setStyleSheet("background-color: #f9e2af; color: #11111b; font-weight: bold; padding: 8px;")
        btn_countdown.clicked.connect(self.start_countdown)

        btn_sell = QPushButton("🔨 SATILDI! (Satışı Bitir) [Enter Tuşu]")
        btn_sell.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 12px; font-size: 16px;")
        btn_sell.clicked.connect(self.sell_product)

        ctrl_layout.addWidget(self.input_bidder)
        ctrl_layout.addWidget(btn_bid)
        ctrl_layout.addWidget(btn_undo)
        ctrl_layout.addWidget(btn_countdown)
        ctrl_layout.addWidget(btn_sell)
        ctrl_box.setLayout(ctrl_layout)
        left_layout.addWidget(ctrl_box)

        new_prod_box = QGroupBox("Sıradaki Ürünü Canlıya Al")
        new_prod_box.setStyleSheet("color: #a6adc8; font-weight: bold;")
        new_prod_layout = QHBoxLayout()

        self.input_new_title = QLineEdit()
        self.input_new_title.setPlaceholderText("Ürün Adı")
        self.input_new_title.setStyleSheet("background-color: #313244; color: #ffffff; padding: 6px;")

        self.input_new_price = QLineEdit()
        self.input_new_price.setPlaceholderText("Başlangıç (₺)")
        self.input_new_price.setStyleSheet("background-color: #313244; color: #ffffff; padding: 6px;")

        btn_start_new = QPushButton("🚀 Ürünü Aç")
        btn_start_new.setStyleSheet("background-color: #cba6f7; color: #11111b; font-weight: bold; padding: 6px;")
        btn_start_new.clicked.connect(self.start_new_product)

        new_prod_layout.addWidget(self.input_new_title)
        new_prod_layout.addWidget(self.input_new_price)
        new_prod_layout.addWidget(btn_start_new)
        new_prod_box.setLayout(new_prod_layout)
        left_layout.addWidget(new_prod_box)

        main_layout.addLayout(left_layout, 60)

        right_layout = QVBoxLayout()

        log_box = QGroupBox("📜 Canlı Pey Akışı")
        log_box.setStyleSheet("color: #a6adc8; font-weight: bold;")
        log_layout = QVBoxLayout()

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #181825; color: #89b4fa; font-family: Consolas; font-size: 13px;")
        log_layout.addWidget(self.txt_log)
        log_box.setLayout(log_layout)
        right_layout.addWidget(log_box)

        btn_whatsapp = QPushButton("💬 WhatsApp Sipariş Mesajı Oluştur")
        btn_whatsapp.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 10px; font-size: 14px;")
        btn_whatsapp.clicked.connect(self.generate_whatsapp_link)
        right_layout.addWidget(btn_whatsapp)

        main_layout.addLayout(right_layout, 40)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.add_manual_bid()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.sell_product()

    def update_server_url(self):
        self.server_url = self.url_input.text().strip('/')

    def get_status(self):
        try:
            r = requests.get(f"{self.server_url}/api/durum", timeout=2)
            if r.status_code == 200:
                data = r.json()
                self.lbl_product.setText(f"📦 Ürün: {data.get('urun_adi', '-')}")
                self.lbl_price.setText(f"{data.get('fiyat', 0):.2f} ₺")
                self.lbl_bidder.setText(f"Son Pey Veren: {data.get('son_pey_veren', '-')}")
                
                if data.get('satildi'):
                    self.lbl_status.setText("🔨 SATILDI!")
                    self.lbl_status.setStyleSheet("color: #f38ba8;")
                else:
                    self.lbl_status.setText("DURUM: AKTİF")
                    self.lbl_status.setStyleSheet("color: #89b4fa;")

                history = data.get('gecmis', [])
                if history != self.bid_history:
                    self.bid_history = history
                    self.txt_log.clear()
                    for item in reversed(history):
                        self.txt_log.append(f"⚡ {item.get('isim', 'Anonim')} -> {item.get('fiyat', 0)} ₺")
        except:
            pass

    def add_manual_bid(self):
        name = self.input_bidder.text().strip() or "Admin Pey"
        try:
            requests.post(f"{self.server_url}/api/pey_ver", json={"isim": name}, timeout=2)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Pey gönderilemedi: {e}")

    def undo_bid(self):
        try:
            requests.post(f"{self.server_url}/api/geri_al", timeout=2)
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", "Geri alma işlemi başarısız.")

    def start_countdown(self):
        self.countdown_val = 3
        self.countdown_timer.start(1000)

    def update_countdown(self):
        if self.countdown_val > 0:
            self.lbl_status.setText(f"⏳ SATILIYOR... {self.countdown_val}")
            self.lbl_status.setStyleSheet("color: #fab387;")
            self.countdown_val -= 1
        else:
            self.countdown_timer.stop()
            self.sell_product()

    def sell_product(self):
        try:
            requests.post(f"{self.server_url}/api/satisi_bitir", timeout=2)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Satış bitirilemedi: {e}")

    def start_new_product(self):
        title = self.input_new_title.text().strip()
        price = self.input_new_price.text().strip()

        if not title or not price:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen ürün adı ve başlangıç fiyatını girin.")
            return

        try:
            payload = {"urun_adi": title, "baslangic_fiyati": float(price)}
            requests.post(f"{self.server_url}/api/yeni_urun", json=payload, timeout=2)
            self.input_new_title.clear()
            self.input_new_price.clear()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yeni ürün açılamadı: {e}")

    def generate_whatsapp_link(self):
        product = self.lbl_product.text().replace("📦 Ürün: ", "")
        bidder = self.lbl_bidder.text().replace("Son Pey Veren: ", "")
        price = self.lbl_price.text()

        if bidder == "-" or "SATILDI" not in self.lbl_status.text():
            QMessageBox.information(self, "Bilgi", "Satış henüz tamamlanmadı veya kazanan yok.")
            return

        msg = f"Tebrikler {bidder}! 🎉\n\nMezatımızdan kazandığınız ürün: *{product}*\nToplam Tutar: *{price}*\n\nÖdeme ve kargo detayları için bu mesaja dönüş yapabilirsiniz."
        url = f"https://wa.me/?text={quote(msg)}"
        webbrowser.open(url)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MezatAdminPanel()
    window.show()
    sys.exit(app.exec_())