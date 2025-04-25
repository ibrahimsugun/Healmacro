"""
Knight Online Otomatik İyileştirme ve Buff Sistemi - Ayarlar Yöneticisi
Bu modül, sistemin ayarlarını yönetir ve yapılandırma dosyalarını işler.
"""

import os
import logging
import configparser
import json
from typing import Dict, Any, Optional, List, Tuple

# Logging yapılandırması
logger = logging.getLogger("SettingsManager")

class SettingsManager:
    """Ayarlar ve yapılandırma dosyaları için yönetici sınıf."""
    
    def __init__(self, config_file: str = "settings.ini", buffs_file: str = "buffs.json"):
        """
        SettingsManager sınıfını başlatır.
        
        Args:
            config_file: Yapılandırma dosyası adı.
            buffs_file: Buff'lar için JSON dosyası adı.
        """
        self.config_file = config_file
        self.buffs_file = buffs_file
        self.config = configparser.ConfigParser()
        
        # Yedek dosya adları
        self.backup_config_file = f"{config_file}.bak"
        self.backup_buffs_file = f"{buffs_file}.bak"
        
        # Dosyalar varsa yükle
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Yapılandırma dosyasını yükler.
        
        Returns:
            bool: Yükleme başarılı ise True, değilse False.
        """
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                logger.info(f"Yapılandırma dosyası başarıyla yüklendi: {self.config_file}")
                
                # AutoHealBuff bölümü yoksa oluştur
                if not self.config.has_section('AutoHealBuff'):
                    self.config.add_section('AutoHealBuff')
                
                return True
            else:
                # İlk çalıştırma, yeni bir dosya oluştur
                logger.info(f"Yapılandırma dosyası bulunamadı, yeni oluşturuluyor: {self.config_file}")
                self.config.add_section('AutoHealBuff')
                self.save_config()
                return False
        except Exception as e:
            logger.error(f"Yapılandırma dosyası yüklenirken hata oluştu: {e}")
            
            # Yedek dosyayı deneme
            if os.path.exists(self.backup_config_file):
                try:
                    self.config.read(self.backup_config_file)
                    logger.info(f"Yedek yapılandırma dosyası başarıyla yüklendi: {self.backup_config_file}")
                    return True
                except:
                    logger.error("Yedek yapılandırma dosyası da yüklenemedi.")
            
            return False
    
    def save_config(self) -> bool:
        """
        Yapılandırma dosyasını kaydeder.
        
        Returns:
            bool: Kaydetme başarılı ise True, değilse False.
        """
        try:
            # Önce yedek al (varsa)
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as src, open(self.backup_config_file, 'w') as dst:
                        dst.write(src.read())
                    logger.info(f"Yapılandırma dosyası yedeklendi: {self.backup_config_file}")
                except Exception as backup_err:
                    logger.warning(f"Yapılandırma dosyası yedeklenirken hata: {backup_err}")
            
            # Yapılandırmayı kaydet
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            
            logger.info(f"Yapılandırma dosyası başarıyla kaydedildi: {self.config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Yapılandırma dosyası kaydedilirken hata oluştu: {e}")
            return False
    
    def get_config_section(self, section: str) -> Dict[str, str]:
        """
        Belirli bir bölümün ayarlarını döndürür.
        
        Args:
            section: Bölüm adı.
            
        Returns:
            Dict[str, str]: Bölüm ayarları.
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        return dict(self.config[section])
    
    def update_config_section(self, section: str, settings: Dict[str, str]) -> None:
        """
        Belirli bir bölümün ayarlarını günceller.
        
        Args:
            section: Bölüm adı.
            settings: Yeni ayarlar.
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        # Ayarları güncelle
        for key, value in settings.items():
            self.config[section][key] = value
    
    def load_buffs(self) -> List[Dict[str, Any]]:
        """
        Buff'ları JSON dosyasından yükler.
        
        Returns:
            List[Dict[str, Any]]: Buff'ların listesi.
        """
        buffs_data = []
        
        try:
            if os.path.exists(self.buffs_file):
                # JSON dosyasından verileri oku
                with open(self.buffs_file, "r", encoding="utf-8") as f:
                    try:
                        buffs_data = json.load(f)
                        logger.info(f"Buff'lar başarıyla yüklendi: {self.buffs_file}")
                    except json.JSONDecodeError as json_err:
                        error_msg = f"Dosya geçerli bir JSON formatı değil: {str(json_err)}"
                        logger.error(error_msg)
                        
                        # Yedek dosya dene
                        if os.path.exists(self.backup_buffs_file):
                            try:
                                with open(self.backup_buffs_file, "r", encoding="utf-8") as backup:
                                    buffs_data = json.load(backup)
                                    logger.info(f"Yedek dosyadan veriler başarıyla yüklendi: {self.backup_buffs_file}")
                            except:
                                logger.error("Yedek dosya da geçerli JSON formatında değil.")
        except Exception as e:
            logger.error(f"Buff'lar yüklenirken hata oluştu: {e}")
        
        # Veri türü kontrolü
        if not isinstance(buffs_data, list):
            logger.error(f"Geçersiz veri formatı: Beklenen liste, alınan {type(buffs_data)}")
            buffs_data = []
        
        return buffs_data
    
    def save_buffs(self, buffs_data: List[Dict[str, Any]]) -> bool:
        """
        Buff'ları JSON dosyasına kaydeder.
        
        Args:
            buffs_data: Kaydedilecek buff'ların listesi.
            
        Returns:
            bool: Kaydetme başarılı ise True, değilse False.
        """
        try:
            # Önce yedek al (varsa)
            if os.path.exists(self.buffs_file):
                try:
                    with open(self.buffs_file, 'r', encoding="utf-8") as src, open(self.backup_buffs_file, 'w', encoding="utf-8") as dst:
                        dst.write(src.read())
                    logger.info(f"Buff dosyası yedeklendi: {self.backup_buffs_file}")
                except Exception as backup_err:
                    logger.warning(f"Buff dosyası yedeklenirken hata: {backup_err}")
            
            # Buff'ları kaydet
            with open(self.buffs_file, 'w', encoding="utf-8") as f:
                json.dump(buffs_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Buff'lar başarıyla kaydedildi: {self.buffs_file}")
            return True
        
        except Exception as e:
            logger.error(f"Buff'lar kaydedilirken hata oluştu: {e}")
            return False 