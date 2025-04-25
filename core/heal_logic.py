"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - İyileştirme Mantığı
Bu modül, HP barlarının takibi ve otomatik iyileştirme işlemlerini içerir.
"""

import time
import threading
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional, Callable
from datetime import datetime
from PIL import Image

# Logging yapılandırması
logger = logging.getLogger("HealLogic")

# HP barı renk kodu olarak #AE0000 kullan - RGB formatına dönüştür
HP_BAR_COLOR = {
    'r': 0xAE,  # 174 decimal
    'g': 0x00,  # 0 decimal
    'b': 0x00   # 0 decimal
}

# Renk toleransı (renk farklılıklarını dikkate almak için)
COLOR_TOLERANCE = 30

class HealHelper:
    """
    Knight Online oyununda otomatik iyileştirme işlemlerini yöneten sınıf.
    Bu sınıf, belirli satırlardaki HP barlarını izler ve gerektiğinde iyileştirme yapar.
    """
    
    def __init__(self, click_callback, key_press_callback, screenshot_callback, parent=None):
        """
        HealHelper sınıfını başlatır.
        
        Args:
            click_callback (function): Fare tıklama işlevini sağlayan callback.
            key_press_callback (function): Tuş basma işlevini sağlayan callback.
            screenshot_callback (function): Ekran görüntüsü alma işlevini sağlayan callback.
            parent (object, optional): Üst nesne referansı.
        """
        self.click_callback = click_callback
        self.key_press_callback = key_press_callback
        self.screenshot_callback = screenshot_callback
        self.parent = parent
        
        # Durum değişkenleri
        self.running = False
        self.thread = None
        self.active = False
        self.heal_key = "1"
        self.heal_percentage = 80
        
        # Toplu iyileştirme ayarları
        self.mass_heal_active = False
        self.mass_heal_key = "2"
        self.mass_heal_percentage = 60
        self.party_check_enabled = False
        
        # Satır ayarları (en fazla 8 satır)
        self.rows = []
        for _ in range(8):
            self.rows.append({
                "active": False,
                "coords": [],  # [x1, y1, x2, y2] - Sol üst köşe ve sağ alt köşe koordinatları
                "last_hp_percentage": 100,
                "last_heal_time": datetime.now()
            })
        
        # Zamanlayıcı ayarları
        self.check_interval = 0.1  # saniye
        self.heal_cooldown = 1.0  # saniye
        self.mass_heal_cooldown = 3.0  # saniye
        self.last_check_time = datetime.now()
        self.last_mass_heal_time = datetime.now()
        
        # Hata sayacı
        self.error_count = 0
        self.max_errors = 10
        
        logging.info("HealHelper başlatıldı.")
    
    def start(self):
        """İyileştirme sistemini başlatır."""
        if self.running:
            logging.warning("HealHelper zaten çalışıyor.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logging.info("HealHelper çalışma döngüsü başlatıldı.")
    
    def stop(self):
        """İyileştirme sistemini durdurur."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        logging.info("HealHelper durduruldu.")
    
    def set_active(self, active):
        """
        İyileştirme sisteminin aktif durumunu ayarlar.
        
        Args:
            active (bool): Aktif durumu.
        """
        self.active = active
        logging.info(f"HealHelper aktif durumu: {active}")
    
    def set_heal_key(self, key):
        """
        İyileştirme tuşunu ayarlar.
        
        Args:
            key (str): İyileştirme tuşu.
        """
        self.heal_key = key
        logging.info(f"İyileştirme tuşu: {key}")
    
    def set_heal_percentage(self, percentage):
        """
        İyileştirme eşik yüzdesini ayarlar.
        
        Args:
            percentage (int): İyileştirme yapılacak HP yüzdesi eşiği.
        """
        self.heal_percentage = percentage
        logging.info(f"İyileştirme yüzdesi: {percentage}")
    
    def set_mass_heal_active(self, active):
        """
        Toplu iyileştirme özelliğinin aktif durumunu ayarlar.
        
        Args:
            active (bool): Aktif durumu.
        """
        self.mass_heal_active = active
        logging.info(f"Toplu iyileştirme aktif durumu: {active}")
    
    def set_mass_heal_key(self, key):
        """
        Toplu iyileştirme tuşunu ayarlar.
        
        Args:
            key (str): Toplu iyileştirme tuşu.
        """
        self.mass_heal_key = key
        logging.info(f"Toplu iyileştirme tuşu: {key}")
    
    def set_mass_heal_percentage(self, percentage):
        """
        Toplu iyileştirme eşik yüzdesini ayarlar.
        
        Args:
            percentage (int): Toplu iyileştirme yapılacak HP yüzdesi eşiği.
        """
        self.mass_heal_percentage = percentage
        logging.info(f"Toplu iyileştirme yüzdesi: {percentage}")
    
    def set_party_check_enabled(self, enabled):
        """
        Parti kontrolü özelliğinin aktif durumunu ayarlar.
        
        Args:
            enabled (bool): Aktif durumu.
        """
        self.party_check_enabled = enabled
        logging.info(f"Parti kontrolü aktif durumu: {enabled}")
    
    def set_row_active(self, row_index, active):
        """
        Bir satırın aktif durumunu ayarlar.
        
        Args:
            row_index (int): Satır indeksi.
            active (bool): Aktif durumu.
        """
        if 0 <= row_index < len(self.rows):
            self.rows[row_index]["active"] = active
            logging.info(f"Satır {row_index + 1} aktif durumu: {active}")
    
    def set_row_coords(self, row_index, coords):
        """
        Bir satırın koordinatlarını ayarlar.
        
        Args:
            row_index (int): Satır indeksi.
            coords (list): [x1, y1, x2, y2] formatında koordinatlar.
        """
        if 0 <= row_index < len(self.rows) and len(coords) == 4:
            self.rows[row_index]["coords"] = coords
            logging.info(f"Satır {row_index + 1} koordinatları ayarlandı: {coords}")
    
    def _run_loop(self):
        """İyileştirme döngüsünü çalıştırır."""
        self.error_count = 0
        
        while self.running:
            try:
                # Aktif değilse bekle ve devam et
                if not self.active and not self.mass_heal_active:
                    time.sleep(0.5)
                    continue
                
                # Çok sık kontrol etmeyi önle
                current_time = datetime.now()
                time_diff = (current_time - self.last_check_time).total_seconds()
                if time_diff < self.check_interval:
                    time.sleep(self.check_interval - time_diff)
                    continue
                
                self.last_check_time = current_time
                
                # Ekran görüntüsü al
                screenshot = self.screenshot_callback()
                
                # Her satırı kontrol et
                low_hp_rows = 0
                for row_index, row in enumerate(self.rows):
                    if not row["active"] or len(row["coords"]) != 4:
                        continue
                    
                    # Satır koordinatlarını al
                    x1, y1, x2, y2 = row["coords"]
                    
                    # HP barını kırp
                    # NumPy dizisini direkt dilimleyerek kırpma işlemi yap
                    hp_bar = screenshot[y1:y2, x1:x2]
                    
                    # Eğer gerekiyorsa PIL.Image'e dönüştür
                    if not isinstance(hp_bar, Image.Image):
                        hp_bar = Image.fromarray(hp_bar)
                    
                    # HP yüzdesini hesapla
                    hp_percentage = self._calculate_hp_percentage(hp_bar)
                    
                    # Değerleri güncelle
                    row["last_hp_percentage"] = hp_percentage
                    
                    # Düşük HP kontrolü
                    if hp_percentage <= self.heal_percentage:
                        low_hp_rows += 1
                        
                        # Tek iyileştirme yapılacaksa
                        if self.active:
                            heal_time_diff = (current_time - row["last_heal_time"]).total_seconds()
                            
                            # Bekleme süresi dolmuşsa iyileştir
                            if heal_time_diff >= self.heal_cooldown:
                                # Ortaya tıkla
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                self.click_callback(center_x, center_y)
                                
                                # İyileştirme tuşuna bas
                                time.sleep(0.1)  # Biraz bekle
                                self.key_press_callback(self.heal_key)
                                
                                # Son iyileştirme zamanını güncelle
                                row["last_heal_time"] = current_time
                                
                                logging.info(f"Satır {row_index + 1} iyileştirildi (HP: %{hp_percentage}).")
                
                # Toplu iyileştirme kontrolü
                if self.mass_heal_active and low_hp_rows > 0:
                    mass_heal_time_diff = (current_time - self.last_mass_heal_time).total_seconds()
                    
                    # Parti kontrolü aktifse ve birden fazla düşük HP satırı varsa veya
                    # Parti kontrolü aktif değilse ve en az bir düşük HP satırı varsa
                    if ((self.party_check_enabled and low_hp_rows >= 2) or 
                        (not self.party_check_enabled and low_hp_rows >= 1)):
                        
                        # Bekleme süresi dolmuşsa toplu iyileştir
                        if mass_heal_time_diff >= self.mass_heal_cooldown:
                            # Toplu iyileştirme tuşuna bas
                            self.key_press_callback(self.mass_heal_key)
                            
                            # Son toplu iyileştirme zamanını güncelle
                            self.last_mass_heal_time = current_time
                            
                            logging.info(f"Toplu iyileştirme yapıldı ({low_hp_rows} satır düşük HP).")
                
                # Hata sayacını sıfırla, başarılı işlem
                self.error_count = 0
                
            except Exception as e:
                self.error_count += 1
                logging.error(f"İyileştirme döngüsünde hata: {e}")
                
                # Çok fazla hata varsa durdur
                if self.error_count >= self.max_errors:
                    logging.critical(f"Çok fazla hata oluştu ({self.error_count}), döngü durduruluyor.")
                    self.running = False
                    break
                
                # Hata sonrası bekle
                time.sleep(1.0)
    
    def _calculate_hp_percentage(self, hp_bar_image):
        """
        HP barından HP yüzdesini hesaplar.
        
        Args:
            hp_bar_image (PIL.Image or numpy.ndarray): HP barı görüntüsü.
        
        Returns:
            float: HP yüzdesi (0-100 arası).
        """
        try:
            # Eğer gelen görüntü PIL.Image ise NumPy dizisine dönüştür
            if isinstance(hp_bar_image, Image.Image):
                img_array = np.array(hp_bar_image)
            else:
                # Zaten NumPy dizisi
                img_array = hp_bar_image
            
            # Kırmızı piksel maskeleme (HP barı genellikle kırmızıdır)
            # RGB değerleri için eşik değerleri
            red_mask = (img_array[:, :, 0] > 150) & (img_array[:, :, 1] < 100) & (img_array[:, :, 2] < 100)
            
            # Toplam piksel sayısı ve kırmızı piksel sayısı
            total_pixels = red_mask.size
            red_pixels = np.sum(red_mask)
            
            # HP yüzdesi hesapla
            if total_pixels > 0:
                hp_percentage = (red_pixels / total_pixels) * 100
            else:
                hp_percentage = 0
            
            # Sınırlandırma (0-100 arası)
            hp_percentage = max(0, min(100, hp_percentage))
            
            return hp_percentage
            
        except Exception as e:
            logging.error(f"HP yüzdesi hesaplanırken hata: {e}")
            return 100  # Hata durumunda güvenli değer 