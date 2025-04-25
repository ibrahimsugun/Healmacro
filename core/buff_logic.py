"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - Buff Mantığı
Bu modül, buff sürelerinin takibi ve otomatik kullanımı işlemlerini içerir.
"""

import time
import threading
import logging
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime

# Logging yapılandırması
logger = logging.getLogger("BuffLogic")

class BuffHelper:
    """
    Knight Online oyununda otomatik buff işlemlerini yöneten sınıf.
    Bu sınıf, belirli aralıklarla buff yapmak için bir zamanlayıcı mantığı kullanır.
    """
    
    def __init__(self, key_press_callback, parent=None):
        """
        BuffHelper sınıfını başlatır.
        
        Args:
            key_press_callback (function): Tuş basma işlevini sağlayan callback.
            parent (object, optional): Üst nesne referansı.
        """
        self.key_press_callback = key_press_callback
        self.parent = parent
        
        # Durum değişkenleri
        self.running = False
        self.thread = None
        self.active = False
        
        # Buff tanımları
        self.buffs = []
        for _ in range(10):  # En fazla 10 buff tanımlanabilir
            self.buffs.append({
                "active": False,
                "key": "",
                "interval": 60,  # saniye cinsinden aralık (varsayılan 1 dakika)
                "last_buff_time": datetime.now()
            })
        
        # Hata sayacı
        self.error_count = 0
        self.max_errors = 10
        
        logging.info("BuffHelper başlatıldı.")
    
    def start(self):
        """Buff sistemini başlatır."""
        if self.running:
            logging.warning("BuffHelper zaten çalışıyor.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logging.info("BuffHelper çalışma döngüsü başlatıldı.")
    
    def stop(self):
        """Buff sistemini durdurur."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        logging.info("BuffHelper durduruldu.")
    
    def set_active(self, active):
        """
        Buff sisteminin aktif durumunu ayarlar.
        
        Args:
            active (bool): Aktif durumu.
        """
        self.active = active
        logging.info(f"BuffHelper aktif durumu: {active}")
    
    def set_buff_active(self, buff_index, active):
        """
        Bir buff'ın aktif durumunu ayarlar.
        
        Args:
            buff_index (int): Buff indeksi.
            active (bool): Aktif durumu.
        """
        if 0 <= buff_index < len(self.buffs):
            self.buffs[buff_index]["active"] = active
            logging.info(f"Buff {buff_index + 1} aktif durumu: {active}")
    
    def set_buff_key(self, buff_index, key):
        """
        Bir buff'ın tuşunu ayarlar.
        
        Args:
            buff_index (int): Buff indeksi.
            key (str): Buff tuşu.
        """
        if 0 <= buff_index < len(self.buffs):
            self.buffs[buff_index]["key"] = key
            logging.info(f"Buff {buff_index + 1} tuşu: {key}")
    
    def set_buff_interval(self, buff_index, interval):
        """
        Bir buff'ın aralığını saniye cinsinden ayarlar.
        
        Args:
            buff_index (int): Buff indeksi.
            interval (int): Saniye cinsinden aralık.
        """
        if 0 <= buff_index < len(self.buffs) and interval > 0:
            self.buffs[buff_index]["interval"] = interval
            logging.info(f"Buff {buff_index + 1} aralığı: {interval} saniye")
    
    def reset_buff_timer(self, buff_index):
        """
        Bir buff'ın zamanlayıcısını sıfırlar.
        
        Args:
            buff_index (int): Buff indeksi.
        """
        if 0 <= buff_index < len(self.buffs):
            self.buffs[buff_index]["last_buff_time"] = datetime.now()
            logging.info(f"Buff {buff_index + 1} zamanlayıcısı sıfırlandı.")
    
    def _run_loop(self):
        """Buff döngüsünü çalıştırır."""
        self.error_count = 0
        
        while self.running:
            try:
                # Aktif değilse bekle ve devam et
                if not self.active:
                    time.sleep(1.0)
                    continue
                
                current_time = datetime.now()
                
                # Her bir buff'ı kontrol et
                for buff_index, buff in enumerate(self.buffs):
                    if not buff["active"] or not buff["key"]:
                        continue
                    
                    # Aralık kontrolü
                    time_diff = (current_time - buff["last_buff_time"]).total_seconds()
                    
                    # Buff zamanı geldiyse buff yap
                    if time_diff >= buff["interval"]:
                        # Buff tuşuna bas
                        self.key_press_callback(buff["key"])
                        
                        # Son buff zamanını güncelle
                        buff["last_buff_time"] = current_time
                        
                        logging.info(f"Buff {buff_index + 1} yapıldı (tuş: {buff['key']}).")
                        
                        # Bufflar arası bekleme süresi
                        time.sleep(0.5)
                
                # Hata sayacını sıfırla, başarılı işlem
                self.error_count = 0
                
                # Döngü aralığı (1 saniye)
                time.sleep(1.0)
                
            except Exception as e:
                self.error_count += 1
                logging.error(f"Buff döngüsünde hata: {e}")
                
                # Çok fazla hata varsa durdur
                if self.error_count >= self.max_errors:
                    logging.critical(f"Çok fazla hata oluştu ({self.error_count}), döngü durduruluyor.")
                    self.running = False
                    break
                
                # Hata sonrası bekle
                time.sleep(1.0)

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