import base64
import os
from cryptography.fernet import Fernet
from flask import current_app
from typing import Optional

class CryptoUtils:
    """Shifrlash/deshifrlash utilitasi"""
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Yangi shifrlash kaliti yaratish"""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def get_encryption_key() -> Optional[str]:
        """Hozirgi shifrlash kalitini olish"""
        return current_app.config.get('ENCRYPTION_KEY')
    
    @staticmethod
    def encrypt_text(text: str, key: Optional[str] = None) -> str:
        """
        Matnni shifrlash
        
        Args:
            text: Shifrlanadigan matn
            key: Shifrlash kaliti (agar berilmasa, app config dan olinadi)
            
        Returns:
            str: Shirlangan matn (base64 format)
        """
        try:
            if not key:
                key = CryptoUtils.get_encryption_key()
            
            if key:
                fernet = Fernet(key.encode())
                encrypted = fernet.encrypt(text.encode())
                return encrypted.decode()
            else:
                # Fallback - oddiy base64 encoding (development uchun)
                return base64.b64encode(text.encode()).decode()
                
        except Exception:
            # Agar shifrlash muvaffaqiyatsiz bo'lsa, base64 ishlatish
            return base64.b64encode(text.encode()).decode()
    
    @staticmethod
    def decrypt_text(encrypted_text: str, key: Optional[str] = None) -> str:
        """
        Shirlangan matnni deshifrlash
        
        Args:
            encrypted_text: Shirlangan matn
            key: Shifrlash kaliti (agar berilmasa, app config dan olinadi)
            
        Returns:
            str: Deshirlangan matn
        """
        try:
            if not key:
                key = CryptoUtils.get_encryption_key()
            
            if key:
                fernet = Fernet(key.encode())
                decrypted = fernet.decrypt(encrypted_text.encode())
                return decrypted.decode()
            else:
                # Fallback - base64 decoding
                return base64.b64decode(encrypted_text.encode()).decode()
                
        except Exception:
            # Agar deshifrlash muvaffaqiyatsiz bo'lsa, base64 ishlatish
            try:
                return base64.b64decode(encrypted_text.encode()).decode()
            except:
                return encrypted_text  # Asl matnni qaytarish
    
    @staticmethod
    def is_encryption_available() -> bool:
        """Shifrlash imkoniyati mavjudligini tekshirish"""
        return bool(current_app.config.get('ENCRYPTION_KEY'))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Parolni hash qilish (Werkzeug ishlatadi)"""
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password)
    
    @staticmethod
    def check_password(password: str, hash_value: str) -> bool:
        """Parolni tekshirish"""
        from werkzeug.security import check_password_hash
        return check_password_hash(hash_value, password)