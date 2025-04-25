"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - Ana Widget
Bu modül, iyileştirme ve buff sistemi için ana kullanıcı arayüzü bileşenini içerir.
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                           QGroupBox, QLabel, QLineEdit, QSpinBox, QCheckBox, 
                           QSlider, QScrollArea)
from PyQt5.QtCore import Qt

# Kendi modüllerimizi içe aktar
from ui.components.heal_row_widget import HealRowWidget
from ui.components.buff_widget import BuffWidget

# Logging yapılandırması
logger = logging.getLogger("AutoHealBuffWidget")

class AutoHealBuffWidget(QWidget):
    """
    Auto Heal ve Buff sistemini içeren ana widget.
    - Tüm satırlar için ortak heal tuşu kullanır
    - Buff ve AC için zamanlayıcı bazlı çalışır
    """
    def __init__(self, parent=None):
        """
        AutoHealBuffWidget sınıfını başlatır.
        
        Args:
            parent: Üst widget (varsayılan: None).
        """
        super().__init__(parent)
        self.parent = parent
        
        # Statusbar referansını al
        self.statusbar = None
        if hasattr(parent, 'statusbar'):
            self.statusbar = parent.statusbar
        
        # Satır ve buff listeleri
        self.heal_rows = []
        self.buff_widgets = []
        
        # HP yüzdesi ve heal tuşları
        self.heal_percentage = 80
        self.heal_key = "1"
        self.heal_active = False
        
        # Toplu heal ayarları
        self.mass_heal_percentage = 60
        self.mass_heal_key = "2"
        self.mass_heal_active = False
        self.party_check_enabled = False
        
        # Kontrol frekansı ayarları (milisaniye)
        self.heal_check_interval = 500  # 500ms varsayılan değer
        self.buff_check_interval = 500  # 500ms varsayılan değer
        
        # Çalışma durumu
        self.working = False
        
        # UI oluştur
        self.setup_ui()
        
    def setup_ui(self):
        """
        Kullanıcı arayüzü bileşenlerini oluşturur.
        """
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Scroll bölgesi oluştur
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(600)
        
        # Scroll içeriği
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll.setWidget(scroll_content)
        
        # Ayarlar bölümü
        settings_group = QGroupBox("Heal Satırları")
        settings_layout = QVBoxLayout(settings_group)
        
        # HP bar satırları bölümü
        rows_grid = QGridLayout()
        rows_grid.setContentsMargins(5, 10, 5, 10)
        rows_grid.setVerticalSpacing(10)
        
        # HP barı satırlarını oluştur
        for i in range(8):
            row_widget = HealRowWidget(self, i)
            self.heal_rows.append(row_widget)
            rows_grid.addWidget(row_widget, i, 0)
            
            # Koordinat alma butonuna tıklama işlemini bağla
            row_widget.button.clicked.connect(lambda checked, idx=i: self.take_row_coordinates(idx))
        
        settings_layout.addLayout(rows_grid)
        
        # Heal ayarları bölümü
        heal_group = QGroupBox("İyileştirme Ayarları")
        heal_layout = QGridLayout(heal_group)
        
        # HP yüzdesi ayarı
        hp_pct_label = QLabel("HP %:")
        self.hp_pct_slider = QSpinBox()
        self.hp_pct_slider.setRange(1, 99)
        self.hp_pct_slider.setValue(self.heal_percentage)
        self.hp_pct_slider.valueChanged.connect(self.on_hp_percentage_changed)
        self.hp_pct_slider.setToolTip("HP barı bu yüzdeye düştüğünde iyileştirme yapılacak")
        
        # Heal tuşu girişi
        heal_key_label = QLabel("İyileştirme Tuşu:")
        self.heal_key_input = QLineEdit(self.heal_key)
        self.heal_key_input.setMaxLength(3)
        self.heal_key_input.setFixedWidth(50)
        self.heal_key_input.textChanged.connect(self.on_heal_key_changed)
        self.heal_key_input.setToolTip("İyileştirme için kullanılacak tuş")
        
        # İyileştirme aktif/pasif
        self.heal_active_checkbox = QCheckBox("İyileştirme Aktif")
        self.heal_active_checkbox.setChecked(self.heal_active)
        self.heal_active_checkbox.stateChanged.connect(self.on_heal_active_changed)
        self.heal_active_checkbox.setToolTip("İyileştirme sistemini aktifleştirir/devre dışı bırakır")
        
        # Toplu iyileştirme bölümü
        mass_heal_label = QLabel("Toplu İyileştirme:")
        self.mass_heal_active_checkbox = QCheckBox("Aktif")
        self.mass_heal_active_checkbox.setChecked(self.mass_heal_active)
        self.mass_heal_active_checkbox.stateChanged.connect(self.on_mass_heal_active_changed)
        self.mass_heal_active_checkbox.setToolTip("Toplu iyileştirme sistemini aktifleştirir/devre dışı bırakır")
        
        # Toplu iyileştirme tuşu
        mass_heal_key_label = QLabel("Tuş:")
        self.mass_heal_key_input = QLineEdit(self.mass_heal_key)
        self.mass_heal_key_input.setMaxLength(3)
        self.mass_heal_key_input.setFixedWidth(50)
        self.mass_heal_key_input.textChanged.connect(self.on_mass_heal_key_changed)
        self.mass_heal_key_input.setToolTip("Toplu iyileştirme için kullanılacak tuş")
        
        # Toplu iyileştirme yüzdesi
        mass_heal_pct_label = QLabel("HP %:")
        self.mass_heal_pct_slider = QSpinBox()
        self.mass_heal_pct_slider.setRange(1, 99)
        self.mass_heal_pct_slider.setValue(self.mass_heal_percentage)
        self.mass_heal_pct_slider.valueChanged.connect(self.on_mass_heal_percentage_changed)
        self.mass_heal_pct_slider.setToolTip("Grup iyileştirme için HP eşiği")
        
        # Parti kontrolü
        self.party_check_checkbox = QCheckBox("Parti Kontrolü")
        self.party_check_checkbox.setChecked(self.party_check_enabled)
        self.party_check_checkbox.stateChanged.connect(self.on_mass_heal_party_check_changed)
        self.party_check_checkbox.setToolTip("Gruptan önce parti seçimini kontrol eder")
        
        # Grid layout'a widget'ları ekle
        # 1. satır
        heal_layout.addWidget(hp_pct_label, 0, 0)
        heal_layout.addWidget(self.hp_pct_slider, 0, 1)
        heal_layout.addWidget(heal_key_label, 0, 2)
        heal_layout.addWidget(self.heal_key_input, 0, 3)
        heal_layout.addWidget(self.heal_active_checkbox, 0, 4)
        
        # 2. satır
        heal_layout.addWidget(mass_heal_label, 1, 0)
        heal_layout.addWidget(self.mass_heal_active_checkbox, 1, 1)
        heal_layout.addWidget(mass_heal_key_label, 1, 2)
        heal_layout.addWidget(self.mass_heal_key_input, 1, 3)
        
        # 3. satır
        heal_layout.addWidget(mass_heal_pct_label, 2, 0)
        heal_layout.addWidget(self.mass_heal_pct_slider, 2, 1)
        heal_layout.addWidget(self.party_check_checkbox, 2, 2, 1, 2)
        
        settings_layout.addWidget(heal_group)
        
        # Kontrol frekansı grup kutusu
        freq_group = QGroupBox("Kontrol Frekansı")
        freq_layout = QVBoxLayout(freq_group)
        
        # Heal kontrol frekansı
        heal_freq_layout = QHBoxLayout()
        heal_freq_layout.addWidget(QLabel("İyileştirme kontrol frekansı:"))
        self.heal_freq_slider = QSlider(Qt.Horizontal)
        self.heal_freq_slider.setMinimum(100)
        self.heal_freq_slider.setMaximum(1000)
        self.heal_freq_slider.setValue(self.heal_check_interval)
        self.heal_freq_slider.valueChanged.connect(self.on_heal_freq_changed)
        self.heal_freq_slider.setToolTip("HP barı kontrol frekansı (milisaniye)")
        heal_freq_layout.addWidget(self.heal_freq_slider)
        self.heal_freq_label = QLabel(f"{self.heal_check_interval} ms")
        heal_freq_layout.addWidget(self.heal_freq_label)
        freq_layout.addLayout(heal_freq_layout)
        
        # Buff kontrol frekansı
        buff_freq_layout = QHBoxLayout()
        buff_freq_layout.addWidget(QLabel("Buff kontrol frekansı:"))
        self.buff_freq_slider = QSlider(Qt.Horizontal)
        self.buff_freq_slider.setMinimum(100)
        self.buff_freq_slider.setMaximum(1000)
        self.buff_freq_slider.setValue(self.buff_check_interval)
        self.buff_freq_slider.valueChanged.connect(self.on_buff_freq_changed)
        self.buff_freq_slider.setToolTip("Buff zamanlayıcısı için kontrol frekansı (milisaniye)")
        buff_freq_layout.addWidget(self.buff_freq_slider)
        self.buff_freq_label = QLabel(f"{self.buff_check_interval} ms")
        buff_freq_layout.addWidget(self.buff_freq_label)
        freq_layout.addLayout(buff_freq_layout)
        
        settings_layout.addWidget(freq_group)
        scroll_layout.addWidget(settings_group)
        
        # Buff widget'ları bölümü
        buff_group = QGroupBox("Buff Yönetimi")
        buff_layout = QVBoxLayout(buff_group)
        
        # Buff widget'ları oluştur (Normal Buff ve AC)
        buff_widget = BuffWidget(self, 0, "Normal Buff")
        ac_widget = BuffWidget(self, 1, "AC (Anti-Cheat)")
        
        self.buff_widgets.append(buff_widget)
        self.buff_widgets.append(ac_widget)
        
        buff_layout.addWidget(buff_widget)
        buff_layout.addWidget(ac_widget)
        
        scroll_layout.addWidget(buff_group)
        
        # Ana layout'a scroll area ekle
        main_layout.addWidget(scroll)
        
        # Arayüzü logla
        logger.info("Auto Heal ve Buff arayüzü oluşturuldu.")
        if self.statusbar:
            self.statusbar.showMessage("Hazır", 3000)
            
    def on_heal_active_changed(self, state):
        """
        Heal aktifliği değiştiğinde çağrılır
        
        Args:
            state: Checkbox durumu.
        """
        self.heal_active = (state == Qt.Checked)
        logger.info(f"İyileştirme aktif durumu değişti: {self.heal_active}")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"İyileştirme {'aktif' if self.heal_active else 'pasif'} duruma getirildi", 3000)
    
    def on_heal_key_changed(self, text):
        """
        Heal tuşu değiştiğinde çağrılır
        
        Args:
            text: Yeni tuş değeri.
        """
        self.heal_key = text
        logger.info(f"İyileştirme tuşu '{text}' olarak ayarlandı")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"İyileştirme tuşu '{text}' olarak ayarlandı", 3000)
    
    def on_mass_heal_active_changed(self, state):
        """
        Toplu Heal aktifliği değiştiğinde çağrılır
        
        Args:
            state: Checkbox durumu.
        """
        self.mass_heal_active = (state == Qt.Checked)
        logger.info(f"Toplu iyileştirme aktif durumu değişti: {self.mass_heal_active}")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"Toplu iyileştirme {'aktif' if self.mass_heal_active else 'pasif'} duruma getirildi", 3000)
    
    def on_mass_heal_key_changed(self, text):
        """
        Toplu heal tuşu değiştiğinde çağrılır
        
        Args:
            text: Yeni tuş değeri.
        """
        self.mass_heal_key = text
        logger.info(f"Toplu iyileştirme tuşu '{text}' olarak ayarlandı")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"Toplu iyileştirme tuşu '{text}' olarak ayarlandı", 3000)
    
    def on_mass_heal_percentage_changed(self, value):
        """
        Toplu heal yüzdesi değiştiğinde çağrılır
        
        Args:
            value: Yeni yüzde değeri.
        """
        self.mass_heal_percentage = value
        logger.info(f"Toplu iyileştirme yüzdesi %{value} olarak ayarlandı")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"Toplu iyileştirme yüzdesi %{value} olarak ayarlandı", 3000)
    
    def on_mass_heal_party_check_changed(self, state):
        """
        Toplu heal parti kontrolü değiştiğinde çağrılır
        
        Args:
            state: Checkbox durumu.
        """
        self.party_check_enabled = (state == Qt.Checked)
        logger.info(f"Parti kontrolü {'aktif' if self.party_check_enabled else 'pasif'} olarak ayarlandı")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"Parti kontrolü {'aktif' if self.party_check_enabled else 'pasif'} olarak ayarlandı", 3000)
    
    def on_hp_percentage_changed(self, value):
        """
        HP yüzdesi değiştiğinde çağrılır
        
        Args:
            value: Yeni yüzde değeri.
        """
        self.heal_percentage = value
        logger.info(f"İyileştirme yüzdesi %{value} olarak ayarlandı")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"İyileştirme yüzdesi %{value} olarak ayarlandı", 3000)
    
    def on_heal_freq_changed(self, value):
        """
        Heal kontrol frekansı değiştiğinde çağrılır
        
        Args:
            value: Yeni frekans değeri (milisaniye).
        """
        # Değeri 100'e yuvarla
        value = (value // 100) * 100
        if value < 300:
            value = 300
        elif value > 900:
            value = 900
            
        self.heal_check_interval = value
        if hasattr(self, 'heal_freq_label'):
            self.heal_freq_label.setText(f"{value} ms")
        
        logger.info(f"İyileştirme kontrol frekansı {value} ms olarak ayarlandı")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"İyileştirme kontrol frekansı {value} ms olarak ayarlandı", 3000)
    
    def on_buff_freq_changed(self, value):
        """
        Buff kontrol frekansı değiştiğinde çağrılır
        
        Args:
            value: Yeni frekans değeri (milisaniye).
        """
        # Değeri 100'e yuvarla
        value = (value // 100) * 100
        if value < 300:
            value = 300
        elif value > 900:
            value = 900
            
        self.buff_check_interval = value
        if hasattr(self, 'buff_freq_label'):
            self.buff_freq_label.setText(f"{value} ms")
        
        logger.info(f"Buff kontrol frekansı {value} ms olarak ayarlandı")
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage(f"Buff kontrol frekansı {value} ms olarak ayarlandı", 3000)

    def load_config(self, config_section):
        """
        Konfigürasyon bölümünden ayarları yükler
        
        Args:
            config_section: ConfigParser bölümü
        """
        try:
            # HP yüzdesi
            if 'heal_percentage' in config_section:
                self.heal_percentage = int(config_section['heal_percentage'])
                self.hp_pct_slider.setValue(self.heal_percentage)
            
            # Heal tuşu ve aktiflik
            if 'heal_key' in config_section:
                self.heal_key = config_section['heal_key']
                self.heal_key_input.setText(self.heal_key)
                
            if 'heal_active' in config_section:
                self.heal_active = config_section['heal_active'].lower() == 'true'
                self.heal_active_checkbox.setChecked(self.heal_active)
            
            # Toplu heal yüzdesi, tuşu ve aktiflik
            if 'mass_heal_percentage' in config_section:
                self.mass_heal_percentage = int(config_section['mass_heal_percentage'])
                self.mass_heal_pct_slider.setValue(self.mass_heal_percentage)
                
            if 'mass_heal_key' in config_section:
                self.mass_heal_key = config_section['mass_heal_key']
                self.mass_heal_key_input.setText(self.mass_heal_key)
                
            if 'mass_heal_active' in config_section:
                self.mass_heal_active = config_section['mass_heal_active'].lower() == 'true'
                self.mass_heal_active_checkbox.setChecked(self.mass_heal_active)
            
            # Parti kontrolü
            if 'party_check_enabled' in config_section:
                self.party_check_enabled = config_section['party_check_enabled'].lower() == 'true'
                self.party_check_checkbox.setChecked(self.party_check_enabled)
            
            # Kontrol aralıkları
            if 'heal_check_interval' in config_section:
                self.heal_check_interval = int(config_section['heal_check_interval'])
                self.heal_freq_slider.setValue(self.heal_check_interval)
                
            if 'buff_check_interval' in config_section:
                self.buff_check_interval = int(config_section['buff_check_interval'])
                self.buff_freq_slider.setValue(self.buff_check_interval)
            
            # Satır ayarları
            for i, row in enumerate(self.heal_rows):
                # Eğer yapılandırma bölümü içinde bu satır için ayar varsa
                if f'row_{i}_active' in config_section:
                    row_active = config_section[f'row_{i}_active'].lower() == 'true'
                    row.active = row_active
                    row.active_checkbox.setChecked(row_active)
                
                if f'row_{i}_coords' in config_section:
                    coord_text = config_section[f'row_{i}_coords']
                    try:
                        # '[]' karakterlerini temizle
                        coord_text = coord_text.strip('[]')
                        # Virgüllerle ayır
                        coords = [int(x.strip()) for x in coord_text.split(',')]
                        if len(coords) == 4:
                            row.coords = coords
                            row.coord_label.setText(f"({coords[0]},{coords[1]})-({coords[2]}, {coords[3]})")
                    except:
                        logger.warning(f"Satır {i+1} için geçersiz koordinat formatı")
            
            # Buff widget ayarları
            for i, buff in enumerate(self.buff_widgets):
                # Eğer yapılandırma bölümü içinde bu buff için ayar varsa
                if f'buff_{i}_active' in config_section:
                    buff_active = config_section[f'buff_{i}_active'].lower() == 'true'
                    buff.active = buff_active
                    buff.active_checkbox.setChecked(buff_active)
                
                if f'buff_{i}_key' in config_section:
                    buff.key = config_section[f'buff_{i}_key']
                    buff.key_input.setText(buff.key)
                
                if f'buff_{i}_duration' in config_section:
                    try:
                        buff.duration = int(config_section[f'buff_{i}_duration'])
                        buff.duration_input.setValue(buff.duration)
                    except:
                        logger.warning(f"Buff {i+1} için geçersiz süre formatı")
                
                if f'buff_{i}_name' in config_section:
                    buff.buff_name = config_section[f'buff_{i}_name']
            
            # Log mesajı
            logger.info("Ayarlar başarıyla yüklendi.")
            if self.statusbar:
                self.statusbar.showMessage("Ayarlar başarıyla yüklendi.", 3000)
                
        except Exception as e:
            logger.error(f"Ayarlar yüklenirken hata: {e}")
            if self.statusbar:
                self.statusbar.showMessage(f"Ayarlar yüklenirken hata: {e}", 3000)
                
    def save_config(self, config_section):
        """
        Konfigürasyon bölümüne ayarları kaydeder
        
        Args:
            config_section: ConfigParser bölümü
            
        Returns:
            Güncellenen config_section
        """
        try:
            # HP yüzdesi
            config_section['heal_percentage'] = str(self.heal_percentage)
            
            # Heal tuşu ve aktiflik
            config_section['heal_key'] = self.heal_key
            config_section['heal_active'] = str(self.heal_active)
            
            # Toplu heal yüzdesi, tuşu ve aktiflik
            config_section['mass_heal_percentage'] = str(self.mass_heal_percentage)
            config_section['mass_heal_key'] = self.mass_heal_key
            config_section['mass_heal_active'] = str(self.mass_heal_active)
            
            # Parti kontrolü
            config_section['party_check_enabled'] = str(self.party_check_enabled)
            
            # Kontrol aralıkları
            config_section['heal_check_interval'] = str(self.heal_check_interval)
            config_section['buff_check_interval'] = str(self.buff_check_interval)
            
            # Satır ayarları
            for i, row in enumerate(self.heal_rows):
                config_section[f'row_{i}_active'] = str(row.active)
                config_section[f'row_{i}_coords'] = str(row.coords)
            
            # Buff widget ayarları
            for i, buff in enumerate(self.buff_widgets):
                config_section[f'buff_{i}_active'] = str(buff.active)
                config_section[f'buff_{i}_key'] = buff.key
                config_section[f'buff_{i}_duration'] = str(buff.duration)
                config_section[f'buff_{i}_name'] = buff.buff_name
            
            # Log mesajı
            logger.info("Ayarlar başarıyla kaydedildi.")
            if self.statusbar:
                self.statusbar.showMessage("Ayarlar başarıyla kaydedildi.", 3000)
            
            return config_section
        
        except Exception as e:
            logger.error(f"Ayarlar kaydedilirken hata: {e}")
            if self.statusbar:
                self.statusbar.showMessage(f"Ayarlar kaydedilirken hata: {e}", 3000)
            return config_section
            
    def take_row_coordinates(self, row_index):
        """
        Satır için koordinat alma işlemini başlatır
        
        Args:
            row_index: Koordinat alınacak satır indeksi.
        """
        logger.info(f"Satır {row_index + 1} için koordinat alma işlemi başlatıldı")
        
        # Ana pencere referansını kontrol et ve koordinat alma işlemini başlat
        if self.parent and hasattr(self.parent, 'start_coordinate_capture'):
            self.parent.start_coordinate_capture(row_index)
        else:
            logger.error("Ana pencere referansı bulunamadı veya start_coordinate_capture metodu yok")
            
            # Statusbar mesajını göster
            if self.statusbar:
                self.statusbar.showMessage("Koordinat alma başlatılamadı: Ana pencere referansı yok", 3000)
            
    def set_row_coordinates(self, row_index, x, y):
        """
        Belirli bir satır için koordinatları ayarlar.
        
        Args:
            row_index: Koordinat ayarlanacak satır indeksi.
            x: X koordinatı.
            y: Y koordinatı.
        """
        if 0 <= row_index < len(self.heal_rows):
            row_widget = self.heal_rows[row_index]
            row_widget.set_coordinates([x, y])
            
            coords_str = ""
            if len(row_widget.coords) == 2:
                coords_str = f"SOL ({x}, {y})"
            elif len(row_widget.coords) == 4:
                coords_str = f"TAMAMLANDI: ({row_widget.coords[0]}, {row_widget.coords[1]}) - ({row_widget.coords[2]}, {row_widget.coords[3]})"
                
            logger.info(f"Satır {row_index + 1} koordinatları ayarlandı: {coords_str}")
            
            # Statusbar mesajını göster
            if self.statusbar:
                self.statusbar.showMessage(f"Satır {row_index + 1} koordinatları: {coords_str}", 3000)
                
    def start_working(self):
        """
        Heal ve buff işlemi için gerekli değerleri toplayıp çalıştırır.
        
        Returns:
            (rows_data, heal_data, buffs_data) üçlüsü.
        """
        # Çalışma durumunu aktif yap
        self.working = True
        
        # HP satırlarından veri topla
        rows_data = []
        for row in self.heal_rows:
            row_data = {
                "active": row.active,
                "coords": row.coords
            }
            rows_data.append(row_data)
        
        # Heal ayarlarını topla
        heal_data = {
            "heal_active": self.heal_active,
            "heal_key": self.heal_key,
            "mass_heal_active": self.mass_heal_active,
            "mass_heal_key": self.mass_heal_key,
            "mass_heal_percentage": self.mass_heal_percentage,
            "mass_heal_party_check": self.party_check_enabled
        }
        
        # Buff ayarlarını topla
        buffs_data = {}
        for i, buff_widget in enumerate(self.buff_widgets):
            buffs_data[str(i)] = {
                "name": buff_widget.buff_name,
                "key": buff_widget.get_key(),
                "active": buff_widget.active,
                "duration": buff_widget.get_duration()
            }
            
            # Buff zamanlayıcısını başlat
            if buff_widget.active:
                buff_widget.start_timer()
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage("Otomatik iyileştirme ve buff sistemi çalışıyor...", 5000)
        
        logger.info("AutoHealBuffWidget çalışma durumu: Aktif")
        
        return rows_data, heal_data, buffs_data
    
    def stop_working(self):
        """
        Çalışma durumunu durdurur ve tüm buff zamanlayıcılarını durdurur.
        """
        # Çalışma durumunu güncelle
        self.working = False
        
        # Buff zamanlayıcılarını durdur
        for buff_widget in self.buff_widgets:
            buff_widget.stop_timer()
        
        # Statusbar mesajını göster
        if self.statusbar:
            self.statusbar.showMessage("Otomatik iyileştirme ve buff sistemi durduruldu.", 5000)
            
        logger.info("AutoHealBuffWidget çalışma durumu: Durduruldu") 