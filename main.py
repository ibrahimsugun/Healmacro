"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - Ana Uygulama
Bu modül, Knight Online Otomatik İyileştirme ve Buff Sistemini başlatır.
"""

import sys
import os
import logging
import logging.handlers
import time
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QMessageBox, QStatusBar
from PyQt5.QtCore import QTimer, Qt, QSettings
from PyQt5.QtGui import QCursor
import qdarkstyle

# Modülleri import et
from ui.components.auto_heal_buff_widget import AutoHealBuffWidget
from services.keyboard_mouse_service import KeyboardMouseService
from services.screen_service import ScreenService
from core.heal_logic import HealHelper
from core.buff_logic import BuffHelper
from config.settings_manager import SettingsManager

# Logging yapılandırması
def configure_logging():
    """
    Uygulama için loglamayı yapılandırır.
    """
    # Logs klasörünü oluştur
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Kök logger yapılandırması
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Handler'lar
    # Dosya handler (günlük bazında dönen log dosyaları)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        "logs/auto_heal.log", 
        when='midnight', 
        interval=1, 
        backupCount=7
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Konsol handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Handler'ları logger'a ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Ana pencere sınıfı
class MainWindow(QMainWindow):
    """Ana uygulama penceresi"""
    
    def __init__(self):
        super().__init__()
        
        # Servisler
        self.keyboard_mouse_service = KeyboardMouseService()
        self.screen_service = ScreenService()
        
        # Ayarlar yöneticisi
        self.settings_manager = SettingsManager()
        
        # Ana UI bileşeni
        self.main_widget = AutoHealBuffWidget(self)
        
        # Logic sınıfları
        self.heal_helper = None
        self.buff_helper = None
        
        # Durum değişkenleri
        self.is_running = False
        self.selected_row_index = -1  # Koordinat alma için seçilen satır
        self.coordinate_capture_mode = False
        
        # UI kurulumu
        self.setup_ui()
        
        # Ayarları yükle
        self.load_settings()
        
        # Logla
        logging.info("Knight Online Otomatik İyileştirme ve Buff Sistemi başlatıldı.")
        self.statusBar().showMessage("Knight Online Otomatik İyileştirme ve Buff Sistemi hazır!", 5000)
        
    def setup_ui(self):
        """UI bileşenlerini oluşturur"""
        self.setWindowTitle("Knight Online Otomatik İyileştirme ve Buff Sistemi")
        self.setMinimumSize(800, 600)
        
        # Ana widget'ı ayarla
        self.setCentralWidget(self.main_widget)
        
        # Durum çubuğu
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Menü oluştur
        self.create_menu()
        
        # Kısayol tuşları
        self.setup_shortcuts()
    
    def create_menu(self):
        """Menü çubuğunu oluşturur"""
        # Menü çubuğu
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")
        
        # Kaydet eylemi
        save_action = QAction("Ayarları Kaydet", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_settings)
        file_menu.addAction(save_action)
        
        # Ayır
        file_menu.addSeparator()
        
        # Çıkış eylemi
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Kontrol menüsü
        control_menu = menubar.addMenu("Kontrol")
        
        # Başlat/Durdur eylemi
        self.start_stop_action = QAction("Başlat", self)
        self.start_stop_action.setShortcut("F5")
        self.start_stop_action.triggered.connect(self.toggle_start_stop)
        control_menu.addAction(self.start_stop_action)
        
        # Ayır
        control_menu.addSeparator()
        
        # Koordinat eylem menüsü
        coords_menu = QMenu("Koordinat Al", self)
        
        # Satır için koordinat eylemleri
        for i in range(8):
            action = QAction(f"Satır {i+1} Koordinatları", self)
            action.triggered.connect(lambda checked, idx=i: self.start_coordinate_capture(idx))
            coords_menu.addAction(action)
        
        control_menu.addMenu(coords_menu)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("Yardım")
        
        # Hakkında eylemi
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_shortcuts(self):
        """Kısayol tuşlarını ayarlar"""
        # F10 - Başlat/Durdur
        self.shortcut_start_stop = QTimer(self)
        self.shortcut_start_stop.setSingleShot(True)
        self.shortcut_start_stop.timeout.connect(self.toggle_start_stop)
    
    def save_settings(self):
        """Ayarları kaydeder"""
        try:
            # UI bileşeninden ayarları al
            ui_config = self.main_widget.save_config(self.settings_manager.get_config_section('AutoHealBuff'))
            
            # Ayarlar yöneticisine aktar
            self.settings_manager.update_config_section('AutoHealBuff', ui_config)
            
            # Kaydet
            saved = self.settings_manager.save_config()
            
            # Başarılı mesajı
            if saved:
                self.statusBar().showMessage("Ayarlar başarıyla kaydedildi!", 5000)
                logging.info("Ayarlar başarıyla kaydedildi.")
            else:
                self.statusBar().showMessage("Ayarlar kaydedilirken hata oluştu!", 5000)
                logging.error("Ayarlar kaydedilirken hata oluştu!")
        
        except Exception as e:
            logging.error(f"Ayarlar kaydedilirken hata: {e}")
            self.statusBar().showMessage(f"Hata: {e}", 5000)
    
    def load_settings(self):
        """Ayarları yükler"""
        try:
            # UI bileşenine ayarları yükle
            self.main_widget.load_config(self.settings_manager.get_config_section('AutoHealBuff'))
            
            # Başarılı mesajı
            self.statusBar().showMessage("Ayarlar başarıyla yüklendi!", 5000)
            logging.info("Ayarlar başarıyla yüklendi.")
        
        except Exception as e:
            logging.error(f"Ayarlar yüklenirken hata: {e}")
            self.statusBar().showMessage(f"Hata: {e}", 5000)
    
    def toggle_start_stop(self):
        """Sistemi başlatır veya durdurur"""
        if not self.is_running:
            self.start_system()
        else:
            self.stop_system()
    
    def start_system(self):
        """Heal ve buff sistemini başlatır"""
        try:
            if self.is_running:
                return
            
            # UI bileşeninden yapılandırmayı al
            rows_data, heal_data, buffs_data = self.main_widget.start_working()
            
            logging.info("Sistem başlatılıyor... HealHelper oluşturuluyor.")
            
            # HealHelper'ı oluştur
            self.heal_helper = HealHelper(
                self.keyboard_mouse_service.click,
                self.keyboard_mouse_service.press_key,
                self.screen_service.take_screenshot,
                None  # Pencere referansı gerekirse buraya eklenir
            )
            
            # HealHelper ayarları
            self.heal_helper.set_heal_percentage(heal_data.get("heal_percentage", 80))
            self.heal_helper.set_heal_key(heal_data.get("heal_key", "1"))
            self.heal_helper.set_active(heal_data.get("heal_active", False))
            
            # Toplu heal ayarları
            self.heal_helper.set_mass_heal_percentage(heal_data.get("mass_heal_percentage", 60))
            self.heal_helper.set_mass_heal_key(heal_data.get("mass_heal_key", "2"))
            self.heal_helper.set_mass_heal_active(heal_data.get("mass_heal_active", False))
            self.heal_helper.set_party_check_enabled(heal_data.get("mass_heal_party_check", False))
            
            # Aktif satırları ayarla
            for idx, row_data in enumerate(rows_data):
                if row_data["active"] and len(row_data["coords"]) == 4:
                    logging.info(f"Aktif satır ayarlanıyor: {idx+1}, Koordinatlar: {row_data['coords']}")
                    self.heal_helper.set_row_active(idx, True)
                    self.heal_helper.set_row_coords(idx, row_data["coords"])
            
            logging.info("BuffHelper oluşturuluyor.")
            
            # BuffHelper'ı oluştur
            self.buff_helper = BuffHelper(
                self.keyboard_mouse_service.press_key
            )
            
            # BuffHelper ayarları
            for buff_id, buff_data in buffs_data.items():
                if buff_data["active"]:
                    self.buff_helper.set_buff_active(int(buff_id), True)
                    self.buff_helper.set_buff_key(int(buff_id), buff_data["key"])
                    self.buff_helper.set_buff_duration(int(buff_id), buff_data["duration"])
            
            # HealHelper'ı başlat
            if any(row_data["active"] for row_data in rows_data):
                logging.info("HealHelper başlatılıyor...")
                self.heal_helper.start()
                logging.info("HealHelper başlatıldı!")
            
            # BuffHelper'ı başlat
            if any(buff_data["active"] for buff_id, buff_data in buffs_data.items()):
                logging.info("BuffHelper başlatılıyor...")
                self.buff_helper.start()
                logging.info("BuffHelper başlatıldı!")
            
            # Durumu güncelle
            self.is_running = True
            self.start_stop_action.setText("Durdur")
            
            # Logla
            logging.info("Sistem başlatıldı!")
            self.statusBar().showMessage("Sistem başlatıldı!", 5000)
        
        except Exception as e:
            logging.error(f"Sistem başlatılırken hata: {e}")
            self.statusBar().showMessage(f"Hata: {e}", 5000)
    
    def stop_system(self):
        """Heal ve buff sistemini durdurur"""
        try:
            if not self.is_running:
                return
            
            # HealHelper'ı durdur
            if self.heal_helper:
                self.heal_helper.stop()
                self.heal_helper = None
            
            # BuffHelper'ı durdur
            if self.buff_helper:
                self.buff_helper.stop()
                self.buff_helper = None
            
            # UI bileşeni durumunu güncelle
            self.main_widget.stop_working()
            
            # Durumu güncelle
            self.is_running = False
            self.start_stop_action.setText("Başlat")
            
            # Logla
            logging.info("Sistem durduruldu!")
            self.statusBar().showMessage("Sistem durduruldu!", 5000)
        
        except Exception as e:
            logging.error(f"Sistem durdurulurken hata: {e}")
            self.statusBar().showMessage(f"Hata: {e}", 5000)
    
    def start_coordinate_capture(self, row_index):
        """Koordinat yakalama modunu başlatır"""
        if self.is_running:
            QMessageBox.warning(self, "Uyarı", "Koordinat almak için önce sistemi durdurun!")
            return
        
        self.selected_row_index = row_index
        self.coordinate_capture_mode = True
        
        # Kullanıcıya bilgi ver
        message = f"Satır {row_index + 1} için koordinat alma modu aktif!\n\n"
        message += "1. HP barının SOL ucuna gelin ve CTRL tuşuna basın.\n"
        message += "2. HP barının SAĞ ucuna gelin ve CTRL tuşuna basın.\n"
        message += "3. ESC tuşu ile iptal edebilirsiniz."
        
        QMessageBox.information(self, "Koordinat Al", message)
        
        # Logla
        logging.info(f"Satır {row_index + 1} için koordinat alma modu başlatıldı.")
        self.statusBar().showMessage(f"Satır {row_index + 1} için koordinat alma modu aktif! İlk koordinat için CTRL tuşuna basın.", 0)
    
    def keyPressEvent(self, event):
        """Tuş basma olaylarını yakalar"""
        # Esc tuşu ile koordinat alma modunu iptal et
        if event.key() == Qt.Key_Escape and self.coordinate_capture_mode:
            self.coordinate_capture_mode = False
            self.selected_row_index = -1
            self.statusBar().showMessage("Koordinat alma işlemi iptal edildi!", 3000)
            logging.info("Koordinat alma işlemi kullanıcı tarafından iptal edildi.")
        
        # CTRL tuşu ile koordinat al
        elif event.key() == Qt.Key_Control and self.coordinate_capture_mode and self.selected_row_index >= 0:
            # Fare pozisyonunu al
            cursor_pos = QCursor.pos()
            x, y = cursor_pos.x(), cursor_pos.y()
            
            # Seçilen satır için koordinatları ayarla
            self.main_widget.set_row_coordinates(self.selected_row_index, x, y)
            
            # İlk tıklama ise devam et, ikinci tıklama ise bitir
            if len(self.main_widget.heal_rows[self.selected_row_index].coords) >= 4:
                row_idx = self.selected_row_index + 1
                self.coordinate_capture_mode = False
                self.statusBar().showMessage(f"Satır {row_idx} için koordinatlar başarıyla alındı!", 3000)
                logging.info(f"Satır {row_idx} için koordinatlar başarıyla alındı.")
                self.selected_row_index = -1
            else:
                row_idx = self.selected_row_index + 1
                self.statusBar().showMessage(f"Satır {row_idx} için ilk koordinat alındı: ({x},{y}). Şimdi SAĞ uç için CTRL tuşuna basın.", 0)
                logging.info(f"Satır {row_idx} için ilk koordinat alındı: ({x},{y}).")
        
        # F10 kısayolu için
        elif event.key() == Qt.Key_F10:
            self.shortcut_start_stop.start(100)  # Debounce için 100ms bekle
        
        # Diğer tuşlar için ana sınıfa geç
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Fare tıklama olaylarını yakalar"""
        # Koordinat alma modu aktifse
        if self.coordinate_capture_mode and self.selected_row_index >= 0:
            if event.button() == Qt.LeftButton:
                x, y = event.globalX(), event.globalY()
                
                # Seçilen satır için koordinatları ayarla
                self.main_widget.set_row_coordinates(self.selected_row_index, x, y)
                
                # İlk tıklama ise devam et, ikinci tıklama ise bitir
                if len(self.main_widget.heal_rows[self.selected_row_index].coords) >= 4:
                    self.coordinate_capture_mode = False
                    self.selected_row_index = -1
                    self.statusBar().showMessage("Koordinatlar başarıyla alındı!", 3000)
                else:
                    self.statusBar().showMessage(f"İlk koordinat alındı: ({x},{y}). Şimdi sağ alt köşe için tıklayın.", 0)
        
        # Diğer tıklamalar için ana sınıfa geç
        super().mousePressEvent(event)
    
    def show_about(self):
        """Hakkında mesajını gösterir"""
        about_text = """
        <h2>Knight Online Otomatik İyileştirme ve Buff Sistemi</h2>
        <p>Versiyon 1.0.0</p>
        <p>Bu uygulama Knight Online oyununda otomatik iyileştirme ve
        buff kullanımı için geliştirilmiştir.</p>
        <p>&copy; 2023 - Tüm hakları saklıdır.</p>
        """
        
        QMessageBox.about(self, "Hakkında", about_text)
    
    def closeEvent(self, event):
        """Pencere kapatıldığında"""
        try:
            # Sistem çalışıyorsa durdur
            if self.is_running:
                self.stop_system()
            
            # Ayarları kaydet
            self.save_settings()
            
            # Event'i kabul et
            event.accept()
            
            # Logla
            logging.info("Uygulama kapatıldı.")
        
        except Exception as e:
            logging.error(f"Uygulama kapatılırken hata: {e}")
            event.accept()  # Yine de kapat

# Ana başlatma fonksiyonu
def main():
    """Ana uygulamayı başlatır"""
    # Loglama yapılandırması
    logger = configure_logging()
    
    try:
        # PyQt uygulamasını başlat
        app = QApplication(sys.argv)
        
        # Koyu tema uygula
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        # Ana pencereyi oluştur ve göster
        window = MainWindow()
        window.show()
        
        # Uygulamayı çalıştır
        sys.exit(app.exec_())
    
    except Exception as e:
        logger.error(f"Uygulama başlatılırken kritik hata: {e}", exc_info=True)
        sys.exit(1)

# Doğrudan çalıştırıldığında
if __name__ == "__main__":
    main() 