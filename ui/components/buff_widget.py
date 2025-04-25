"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - Buff Widget'ı
Bu modül, bufflar için kullanıcı arayüzü bileşenini içerir.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QCheckBox, QLabel, QLineEdit, QSpinBox
from PyQt5.QtCore import Qt, QTimer
import logging
import time

# Logging yapılandırması
logger = logging.getLogger("BuffWidget")

# Yardımcı fonksiyonlar
def format_time(seconds: int) -> str:
    """
    Saniye cinsinden süreyi formatlar.
    
    Args:
        seconds: Formatlanacak süre (saniye).
        
    Returns:
        "DD:SS" formatında süre veya "KULLANILDI!" (süre 0 ise).
    """
    if seconds <= 0:
        return "KULLANILDI!"
        
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

class BuffWidget(QWidget):
    """
    Buff yönetimi için kullanılan widget.
    Buff aktifliği, tuşu ve süresini yönetmek için gerekli alanları içerir.
    """
    def __init__(self, parent=None, buff_index=0, buff_name="Buff"):
        """
        BuffWidget sınıfını başlatır.
        
        Args:
            parent: Üst widget (varsayılan: None).
            buff_index: Buff indeksi (0-1).
            buff_name: Buff adı.
        """
        super().__init__(parent)
        self.parent = parent
        self.buff_index = buff_index
        self.buff_name = buff_name
        self.active = False
        self.key = ""
        self.duration = 300  # Varsayılan 5 dakika (300 saniye)
        self.last_used = 0
        self.timer = None
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluşturur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 10, 5, 10)
        
        # Üst satır - Başlık ve aktif/pasif checkbox'ı
        top_row = QHBoxLayout()
        
        # Buff adı
        name_label = QLabel(f"{self.buff_name}")
        name_label.setStyleSheet("font-weight: bold; color: #e67e22;")
        name_label.setToolTip(f"Buff {self.buff_index + 1} adı")
        
        # Aktif/Pasif checkboxı
        self.active_checkbox = QCheckBox("Aktif")
        self.active_checkbox.setChecked(False)
        self.active_checkbox.stateChanged.connect(self.on_active_changed)
        self.active_checkbox.setToolTip(f"{self.buff_name} otomatik kullanımını aktifleştirir/devre dışı bırakır")
        
        top_row.addWidget(name_label)
        top_row.addStretch()
        top_row.addWidget(self.active_checkbox)
        
        # Orta satır - Tuş ve süre
        middle_row = QHBoxLayout()
        
        # Tuş etiketi ve giriş alanı
        key_label = QLabel("Tuş:")
        self.key_input = QLineEdit("F1")
        self.key_input.setMaxLength(3)
        self.key_input.setFixedWidth(50)
        self.key_input.textChanged.connect(self.on_key_changed)
        self.key_input.setToolTip(f"{self.buff_name} için kullanılacak tuş")
        
        # Süre etiketi ve ayar alanı
        duration_label = QLabel("Süre:")
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 3600)  # 1 saniye - 1 saat
        self.duration_input.setValue(300)  # Varsayılan 5 dakika
        self.duration_input.setSingleStep(5)
        self.duration_input.setSuffix(" sn")
        self.duration_input.valueChanged.connect(self.on_duration_changed)
        self.duration_input.setToolTip(f"{self.buff_name} kullanım süresi (saniye)")
        
        middle_row.addWidget(key_label)
        middle_row.addWidget(self.key_input)
        middle_row.addStretch()
        middle_row.addWidget(duration_label)
        middle_row.addWidget(self.duration_input)
        
        # Alt satır - Kalan süre
        bottom_row = QHBoxLayout()
        
        # Kalan süre etiketi
        remaining_label = QLabel("Kalan Süre:")
        self.remaining_value = QLabel("--:--")
        self.remaining_value.setStyleSheet("font-weight: bold;")
        self.remaining_value.setToolTip(f"{self.buff_name} için kalan süre")
        
        bottom_row.addWidget(remaining_label)
        bottom_row.addWidget(self.remaining_value)
        bottom_row.addStretch()
        
        # Ana layout'a ekle
        main_layout.addLayout(top_row)
        main_layout.addLayout(middle_row)
        main_layout.addLayout(bottom_row)
    
    def on_active_changed(self, state):
        """
        Aktif/Pasif durumu değiştiğinde çağrılır
        
        Args:
            state: Checkbox durumu.
        """
        self.active = (state == Qt.Checked)
        logger.info(f"{self.buff_name} aktif durumu değişti: {self.active}")
    
    def on_key_changed(self, text):
        """
        Tuş değiştiğinde çağrılır
        
        Args:
            text: Yeni tuş değeri.
        """
        self.key = text
        logger.info(f"{self.buff_name} tuşu '{text}' olarak ayarlandı")
    
    def on_duration_changed(self, value):
        """
        Süre değiştiğinde çağrılır
        
        Args:
            value: Yeni süre değeri (saniye).
        """
        self.duration = value
        logger.info(f"{self.buff_name} süresi {value} saniye olarak ayarlandı")
    
    def update_timer(self):
        """
        Kalan süreyi hesaplar ve etiketini günceller.
        """
        if not self.active:
            self.remaining_value.setText("--:--")
            return
            
        current_time = time.time()
        elapsed = current_time - self.last_used
        remaining = max(0, self.duration - elapsed)
        
        # Kalan süreyi formatla ve göster
        remaining_text = format_time(int(remaining))
        self.remaining_value.setText(remaining_text)
        
        # Süre dolduğunda rengi değiştir
        if remaining <= 0:
            self.remaining_value.setStyleSheet("font-weight: bold; color: #e74c3c;")
        else:
            self.remaining_value.setStyleSheet("font-weight: bold; color: #27ae60;")
    
    def start_timer(self):
        """
        Buff zamanlayıcısını başlatır.
        """
        if self.timer is None:
            # 1 saniyede bir kalan süreyi güncelle
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_timer)
            self.timer.start(1000)  # 1 saniye
            
            # Başlangıç zamanını ayarla (eğer belirtilmediyse)
            if self.last_used == 0:
                self.last_used = time.time()
                
            logger.info(f"{self.buff_name} zamanlayıcısı başlatıldı")
            
            # İlk güncellemeyi hemen yap
            self.update_timer()
    
    def stop_timer(self):
        """
        Buff zamanlayıcısını durdurur.
        """
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
            logger.info(f"{self.buff_name} zamanlayıcısı durduruldu")
            
            # Son güncellemeyi yap
            self.update_timer()
    
    def get_key(self):
        """Buff tuşunu döndürür."""
        return self.key
    
    def get_duration(self):
        """Buff süresini döndürür."""
        return self.duration 