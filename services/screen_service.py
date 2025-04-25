"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - Ekran Görüntüsü Servisi
Bu modül, ekran görüntüsü alma işlemlerini yönetir.
"""

import os
import time
import logging
import numpy as np
import pyautogui

# Logging yapılandırması
logger = logging.getLogger("ScreenService")

# MSS kütüphanesini dikkatli bir şekilde içe aktar
try:
    import mss.tools
    import mss.windows
    # Windows sürümünü kontrol et ve MSS uyumluluğunu belirle
    import platform
    win_ver = platform.win32_ver()[1]
    # Windows 11 veya üzeri sürümlerde MSS ile bazı sorunlar olabilir
    # Bu durumda MSS yerine PyAutoGUI kullanmayı tercih edebiliriz
    if int(win_ver.split('.')[0]) >= 10 and int(win_ver.split('.')[1]) >= 22000:
        mss_recommended = False
        logger.warning(f"Windows 11 veya üzeri tespit edildi (sürüm: {win_ver}). PyAutoGUI tercih edilecek.")
    else:
        mss_recommended = True
    mss_available = True
    logger.info("MSS kütüphanesi başarıyla içe aktarıldı.")
except ImportError:
    mss_available = False
    mss_recommended = False
    logger.warning("MSS kütüphanesi yüklenemedi. PyAutoGUI kullanılacak.")
except Exception as e:
    mss_available = False
    mss_recommended = False
    logger.warning(f"MSS kütüphanesi yüklenirken hata: {e}")

class ScreenService:
    """Ekran görüntüsü alma işlemlerini yöneten servis."""
    
    def __init__(self, debug_mode=False):
        """
        ScreenService sınıfını başlatır.
        
        Args:
            debug_mode: Hata ayıklama modu etkin mi? (Varsayılan: False)
        """
        self.mss_available = False
        self.sct = None
        self.current_screenshot = None
        self.use_mss = False
        self.debug_mode = debug_mode
        
        # Debug klasörü oluştur
        if self.debug_mode:
            os.makedirs('images', exist_ok=True)
        
        # MSS kütüphanesini başlatmayı dene
        if mss_available and mss_recommended:
            try:
                logger.info("MSS kütüphanesi başlatılıyor...")
                self.sct = mss.mss()
                # Test amaçlı bir ekran görüntüsü almayı dene
                test_img = self.sct.grab(self.sct.monitors[0])
                if test_img:
                    self.mss_available = True
                    self.use_mss = True
                    logger.info("MSS başarıyla başlatıldı ve test edildi.")
                else:
                    logger.warning("MSS test başarısız oldu. PyAutoGUI kullanılacak.")
            except Exception as e:
                logger.error(f"MSS başlatılırken hata: {e}")
                self.sct = None
                
        if not self.mss_available:
            logger.info("PyAutoGUI ekran görüntüsü alma servisi kullanılacak.")
        
    def take_screenshot(self, region=None, target_id=None):
        """
        Belirtilen bölgenin ekran görüntüsünü alır.
        
        Args:
            region: (x, y, width, height) formatında bölge bilgisi.
            target_id: Hedef kimliği (opsiyonel).
            
        Returns:
            numpy.ndarray: Alınan ekran görüntüsü.
        """
        # PyAutoGUI ile ekran görüntüsü alma (varsayılan ve güvenli yöntem)
        try:
            # MSS kütüphanesi kullanma seçeneği etkin ve kullanılabilir değilse
            if not self.use_mss or not self.mss_available:
                if region:
                    x, y, x2, y2 = region
                    width = x2 - x
                    height = y2 - y
                    img = pyautogui.screenshot(region=(x, y, width, height))
                else:
                    img = pyautogui.screenshot()
                
                # PIL görüntüsünü NumPy dizisine dönüştür
                img_np = np.array(img)
                self.current_screenshot = img_np
                
                # Debug modu aktifse görüntüyü kaydet
                self._save_debug_image(img_np, target_id, "pyautogui")
                
                return img_np
            
            # MSS ile ekran görüntüsü alma (daha hızlı ama sorunlu olabilir)
            if region:
                x, y, x2, y2 = region
                width = x2 - x
                height = y2 - y
                
                sct_region = {"top": y, "left": x, "width": width, "height": height}
                
                try:
                    sct_img = self.sct.grab(sct_region)
                    
                    # Numpy dizisine dönüştür
                    img = np.array(sct_img)
                    self.current_screenshot = img
                    
                    # Debug modu aktifse görüntüyü kaydet
                    self._save_debug_image(img, target_id, "mss")
                    
                    logger.debug(f"MSS ile ekran görüntüsü alındı: {region}")
                    return img
                    
                except Exception as mss_error:
                    logger.error(f"MSS ile ekran görüntüsü alınırken hata: {mss_error}")
                    # MSS sorunluysa PyAutoGUI'ye geç ve sonraki işlemlerde MSS'yi kullanma
                    self.use_mss = False
                    self.mss_available = False
                    
                    # PyAutoGUI ile tekrar dene
                    img = pyautogui.screenshot(region=(x, y, width, height))
                    img_np = np.array(img)
                    self.current_screenshot = img_np
                    
                    # Debug modu aktifse görüntüyü kaydet
                    self._save_debug_image(img_np, target_id, "pyautogui_fallback")
                    
                    return img_np
            else:
                # Tüm ekranın görüntüsünü al
                try:
                    if self.use_mss and self.mss_available:
                        sct_img = self.sct.grab(self.sct.monitors[0])
                        img = np.array(sct_img)
                    else:
                        img = np.array(pyautogui.screenshot())
                    
                    self.current_screenshot = img
                    
                    # Debug modu aktifse görüntüyü kaydet
                    self._save_debug_image(img, target_id, "fullscreen")
                    
                    logger.debug("Tüm ekranın görüntüsü alındı.")
                    return img
                except Exception as e:
                    logger.error(f"Tüm ekran görüntüsü alınırken hata: {e}")
                    # MSS sorunluysa PyAutoGUI'ye geç
                    self.use_mss = False
                    
                    # Son bir deneme daha yap
                    try:
                        img = np.array(pyautogui.screenshot())
                        self.current_screenshot = img
                        
                        # Debug modu aktifse görüntüyü kaydet
                        self._save_debug_image(img, target_id, "pyautogui_last_resort")
                        
                        return img
                    except:
                        self.current_screenshot = None
                        return None
                    
        except Exception as e:
            logger.error(f"Ekran görüntüsü alınırken hata: {e}")
            self.current_screenshot = None
            return None
            
    def _save_debug_image(self, img, target_id, source):
        """
        Debug modu aktifse ekran görüntüsünü kaydeder.
        
        Args:
            img: Kaydedilecek görüntü.
            target_id: Hedef kimliği.
            source: Görüntünün kaynağı (mss, pyautogui vb.)
        """
        if not self.debug_mode or img is None:
            return
            
        try:
            debug_file = f"debug_screenshot_{target_id}_{source}_{time.time()}.png"
            from PIL import Image
            img_pil = Image.fromarray(img)
            img_pil.save(os.path.join("images", debug_file))
            logger.debug(f"Debug görüntüsü kaydedildi: {debug_file}")
        except Exception as e:
            logger.error(f"Debug görüntüsü kaydedilirken hata: {e}") 