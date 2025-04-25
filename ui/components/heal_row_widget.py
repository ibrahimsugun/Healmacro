"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - HP Satırı Widget'ı
Bu modül, HP satırları için kullanıcı arayüzü bileşenini içerir.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QPushButton
from PyQt5.QtCore import Qt
import logging

# Logging yapılandırması
logger = logging.getLogger("HealRowWidget")

class HealRowWidget(QWidget):
    """
    Auto Heal sisteminde kullanılan her bir HP satırı için widget.
    Sadece koordinat alma ve aktif/pasif durumu için gerekli alanları içerir.
    """
    def __init__(self, parent=None, row_index=0):
        """
        HealRowWidget sınıfını başlatır.
        
        Args:
            parent: Üst widget (varsayılan: None).
            row_index: Satır indeksi (0-7).
        """
        super().__init__(parent)
        self.parent = parent
        self.row_index = row_index
        self.coords = []  # [x1, y1, x2, y2] - HP barının başlangıç ve bitiş koordinatları
        self.active = False
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluşturur"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Aktif/Pasif checkboxı
        self.active_checkbox = QCheckBox(f"Satır {self.row_index + 1}")
        self.active_checkbox.setChecked(False)
        self.active_checkbox.stateChanged.connect(self.on_active_changed)
        self.active_checkbox.setToolTip(f"Satır {self.row_index + 1} izlemeyi aktifleştirir/devre dışı bırakır")
        
        # Koordinat bilgisi
        self.coord_label = QLabel("Tanımlanmadı")
        self.coord_label.setToolTip("HP barının başlangıç ve bitiş koordinatları")
        
        # Koordinat alma butonu
        self.button = QPushButton("Koordinat Al")
        self.button.setFixedWidth(100)
        self.button.setToolTip("HP barının SOL ve SAĞ koordinatlarını almak için tıklayın")
        
        # Bileşenleri yerleştir
        layout.addWidget(self.active_checkbox)
        layout.addWidget(self.coord_label)
        layout.addWidget(self.button)
    
    def on_active_changed(self, state):
        """
        Aktif/Pasif durumu değiştiğinde çağrılır.
        
        Args:
            state: Checkbox durumu.
        """
        self.active = (state == Qt.Checked)
        logger.info(f"Satır {self.row_index + 1} {'aktif' if self.active else 'pasif'} olarak ayarlandı")
    
    def set_coordinates(self, coords):
        """
        Koordinatları ayarlar ve UI'ı günceller.
        
        Args:
            coords: Koordinatlar [x1, y1, x2, y2] veya [x, y] (tek bir nokta).
        """
        if not self.coords:
            # İlk nokta
            self.coords = [coords[0], coords[1]]
        elif len(self.coords) == 2:
            # İkinci nokta
            self.coords.extend([coords[0], coords[1]])
        elif len(self.coords) == 4:
            # Koordinatlar zaten tam, sıfırla ve ilk noktayı ayarla
            self.coords = [coords[0], coords[1]]
        
        # Koordinat etiketini güncelle
        if len(self.coords) == 4:
            self.coord_label.setText(f"({self.coords[0]},{self.coords[1]})-({self.coords[2]},{self.coords[3]})")
        elif len(self.coords) == 2:
            self.coord_label.setText(f"({self.coords[0]},{self.coords[1]})-(??,??)")
        else:
            self.coord_label.setText("Tanımlanmadı") 