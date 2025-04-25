"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - Klavye ve Fare Servisi
Bu modül, klavye ve fare işlemlerini yönetir.
"""

import os
import time
import logging
import pyautogui

# Logging yapılandırması
logger = logging.getLogger("KeyboardMouseService")

# Win32api için içe aktarma
try:
    import win32api
    import win32con
    win32api_available = True
    logger.info("Win32API başarıyla içe aktarıldı.")
except ImportError:
    win32api_available = False
    logger.warning("Win32API bulunamadı, PyAutoGUI kullanılacak.")

# Tuş basma için interception kütüphanesini içe aktar (varsa)
try:
    from interception import *
    from stroke import *
    from consts import *
    interception_available = True
    logger.info("Interception kütüphanesi başarıyla içe aktarıldı.")
except ImportError:
    interception_available = False
    logger.warning("Interception kütüphanesi bulunamadı, standart yöntemler kullanılacak.")

class KeyboardMouseService:
    """Klavye ve fare işlemlerini yöneten servis."""
    
    def __init__(self):
        """
        KeyboardMouseService sınıfını başlatır.
        Klavye ve fare işlemleri için gereken bileşenleri hazırlar.
        """
        self.keyboard = None
        self.driver = None
        self.keycodes = {
            "F1": 0x3B, "F2": 0x3C, "F3": 0x3D, "F4": 0x3E, "F5": 0x3F, 
            "F6": 0x40, "F7": 0x41, "F8": 0x42, "F9": 0x43, "F10": 0x44, 
            "F11": 0x57, "F12": 0x58, "F13": 0x64, "F14": 0x65, "F15": 0x66, 
            "0": 0x0B, "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, 
            "5": 0x06, "6": 0x07, "7": 0x08, "8": 0x09, "9": 0x0A, 
            "A": 0x1E, "B": 0x30, "C": 0x2E, "D": 0x20, "E": 0x12,
            "F": 0x21, "G": 0x22, "H": 0x23, "I": 0x17, "J": 0x24, 
            "K": 0x25, "L": 0x26, "M": 0x32, "N": 0x31, "O": 0x18, 
            "P": 0x19, "Q": 0x10, "R": 0x13, "S": 0x1F, "T": 0x14, 
            "U": 0x16, "V": 0x2F, "W": 0x11, "X": 0x2D, "Y": 0x15, "Z": 0x2C
        }
        
        # Interception kütüphanesi kullanılabilir ise, başlat
        if interception_available:
            try:
                self.driver = interception()
                for i in range(MAX_DEVICES):
                    if interception.is_keyboard(i):
                        self.keyboard = i
                        logger.info(f"Klavye bulundu: {i}")
                        break
                if self.keyboard is None:
                    logger.warning("Klavye bulunamadı.")
            except Exception as e:
                logger.error(f"Interception sürücüsü yüklenirken hata: {e}")
                self.driver = None
                self.keyboard = None
    
    def click(self, x, y):
        """
        Belirtilen konuma tıklar.
        
        Win32API kullanılabilirse donanım düzeyinde gerçek tıklama yapar,
        yoksa PyAutoGUI kullanır.
        
        Args:
            x: X koordinatı.
            y: Y koordinatı.
        
        Returns:
            bool: İşlemin başarılı olup olmadığı.
        """
        try:
            if win32api_available:
                # Donanım düzeyinde gerçek tıklama yapma (Win32API)
                self.leftclick_win32(x, y)
            else:
                # PyAutoGUI ile tıklama
                pyautogui.click(x, y)
            logger.debug(f"Sol tıklama: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Sol tıklama işlemi başarısız: {e}")
            return False
    
    def right_click(self, x, y):
        """
        Belirtilen konuma sağ tıklar.
        
        Win32API kullanılabilirse donanım düzeyinde gerçek tıklama yapar,
        yoksa PyAutoGUI kullanır.
        
        Args:
            x: X koordinatı.
            y: Y koordinatı.
            
        Returns:
            bool: İşlemin başarılı olup olmadığı.
        """
        try:
            if win32api_available:
                # Donanım düzeyinde gerçek sağ tıklama yapma (Win32API)
                self.rightclick_win32(x, y)
            else:
                # PyAutoGUI ile sağ tıklama
                pyautogui.rightClick(x, y)
            logger.debug(f"Sağ tıklama: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Sağ tıklama işlemi başarısız: {e}")
            return False
    
    def leftclick_win32(self, x, y):
        """
        Win32API kullanarak belirtilen koordinatlarda sol fare tıklaması gerçekleştirir.
        
        Args:
            x: Tıklama x koordinatı
            y: Tıklama y koordinatı
        
        Returns:
            bool: İşlemin başarılı olup olmadığı.
        """
        try:
            # Fare imlecini konumlandır
            win32api.SetCursorPos((x, y))
            # Kısa bekleme
            time.sleep(0.05)
            # Sol tuşa basma olayı
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            # Basma ve bırakma arasında bekleme
            time.sleep(0.1)
            # Sol tuşu bırakma olayı
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            return True
        except Exception as e:
            logger.error(f"Win32API sol tıklama hatası: {e}")
            # Hata durumunda PyAutoGUI ile dene
            pyautogui.click(x, y)
            return False
    
    def rightclick_win32(self, x, y):
        """
        Win32API kullanarak belirtilen koordinatlarda sağ fare tıklaması gerçekleştirir.
        
        Args:
            x: Tıklama x koordinatı
            y: Tıklama y koordinatı
            
        Returns:
            bool: İşlemin başarılı olup olmadığı.
        """
        try:
            # Fare imlecini konumlandır
            win32api.SetCursorPos((x, y))
            # Kısa bekleme
            time.sleep(0.05)
            # Sağ tuşa basma olayı
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
            # Basma ve bırakma arasında bekleme
            time.sleep(0.1)
            # Sağ tuşu bırakma olayı
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
            return True
        except Exception as e:
            logger.error(f"Win32API sağ tıklama hatası: {e}")
            # Hata durumunda PyAutoGUI ile dene
            pyautogui.rightClick(x, y)
            return False
    
    def press_key(self, key, duration=0.01):
        """
        Belirtilen tuşa basar.
        
        Args:
            key: Basılacak tuş.
            duration: Tuşa basılı tutma süresi (saniye).
            
        Returns:
            None
        """
        try:
            # İnterception kütüphanesi kullanılabilir ve sürücü başlatıldı ise
            if interception_available and self.driver is not None and self.keyboard is not None:
                keycode = self.keycodes.get(key.upper(), None)
                if keycode:
                    logger.debug(f"Interception kullanarak tuş basılıyor: {key}")
                    self.tusbas(keycode, duration)
                else:
                    # Keycode bulunamadı, pyautogui kullan
                    logger.debug(f"PyAutoGUI kullanarak tuş basılıyor: {key}")
                    pyautogui.press(key)
            else:
                # Interception yoksa, pyautogui kullan
                logger.debug(f"PyAutoGUI kullanarak tuş basılıyor: {key}")
                pyautogui.press(key)
        except Exception as e:
            logger.error(f"Tuş basma işlemi başarısız: {e}")
    
    def tusbas(self, key, gecikme):
        """
        Belirlenen tuşa basma ve bırakma işlemini gerçekleştiren fonksiyon.
        
        Args:
            key (int): Basılacak tuşun keycode değeri
            gecikme (float): Tuşa basılı tutma süresi (saniye cinsinden)
            
        Returns:
            None
        """
        if not interception_available or self.driver is None or self.keyboard is None:
            logger.error("Interception kullanılamıyor, tuş basılamadı.")
            return
            
        try:
            # Tuşa basma (key down) işlemi
            interception_press = key_stroke(key, interception_key_state.INTERCEPTION_KEY_DOWN.value, 0)
            self.driver.send(self.keyboard, interception_press)
            
            # Tuşa basılı tutma süresi
            time.sleep(gecikme)
            
            # Tuşu bırakma (key up) işlemi
            interception_press.state = interception_key_state.INTERCEPTION_KEY_UP.value
            self.driver.send(self.keyboard, interception_press)
            
            # İki tuş basma arasında minimum bekleme süresi (tuş bırakıldıktan sonra)
            time.sleep(0.01)  # 10ms
            
            logger.debug(f"Interception kullanarak tuş basma başarılı: {key}")
        except Exception as e:
            logger.error(f"Interception ile tuş basma hatası: {e}") 