import re
from typing import Optional, Dict, Any

class Validators:
    """Validatsiya utilitasi"""
    
    @staticmethod
    def validate_uzbek_phone(phone: str) -> Dict[str, Any]:
        """
        O'zbekiston telefon raqami validatsiyasi
        Format: +998XX XXX XX XX
        
        Returns:
            Dict: {'valid': bool, 'message': str, 'formatted': str}
        """
        # Bo'sh joylarni olib tashlash
        clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # +998 bilan boshlanishi kerak
        if not clean_phone.startswith('+998'):
            return {
                'valid': False,
                'message': 'Telefon raqami +998 bilan boshlanishi kerak',
                'formatted': phone
            }
        
        # Umumiy uzunlik 13 bo\'lishi kerak (+998 + 9 raqam)
        if len(clean_phone) != 13:
            return {
                'valid': False,
                'message': 'Telefon raqami 13 ta belgidan iborat bo\'lishi kerak',
                'formatted': phone
            }
        
        # Regex pattern orqali tekshirish
        pattern = r'^\+998[0-9]{9}$'
        if not re.match(pattern, clean_phone):
            return {
                'valid': False,
                'message': 'Telefon raqami formati noto\'g\'ri. Format: +998XX XXX XX XX',
                'formatted': phone
            }
        
        # Formatlangan versiyasini yaratish
        formatted = f"+998{clean_phone[4:6]} {clean_phone[6:9]} {clean_phone[9:11]} {clean_phone[11:13]}"
        
        return {
            'valid': True,
            'message': 'Telefon raqami to\'g\'ri',
            'formatted': formatted
        }
    
    @staticmethod
    def validate_email(email: str) -> Dict[str, Any]:
        """
        Email validatsiyasi
        
        Returns:
            Dict: {'valid': bool, 'message': str}
        """
        if not email:
            return {
                'valid': False,
                'message': 'Email manzil kiritilmagan'
            }
        
        # Email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email.strip().lower()):
            return {
                'valid': False,
                'message': 'Email manzil formati noto\'g\'ri'
            }
        
        return {
            'valid': True,
            'message': 'Email manzil to\'g\'ri'
        }
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """
        Parol validatsiyasi
        
        Returns:
            Dict: {'valid': bool, 'message': str, 'strength': str}
        """
        if not password:
            return {
                'valid': False,
                'message': 'Parol kiritilmagan',
                'strength': 'weak'
            }
        
        issues = []
        strength_score = 0
        
        # Minimum uzunlik
        if len(password) < 8:
            issues.append('Parol kamida 8 ta belgidan iborat bo\'lishi kerak')
        else:
            strength_score += 1
        
        # Katta harf
        if not re.search(r'[A-Z]', password):
            issues.append('Parolda kamida bitta katta harf bo\'lishi kerak')
        else:
            strength_score += 1
        
        # Kichik harf
        if not re.search(r'[a-z]', password):
            issues.append('Parolda kamida bitta kichik harf bo\'lishi kerak')
        else:
            strength_score += 1
        
        # Raqam
        if not re.search(r'[0-9]', password):
            issues.append('Parolda kamida bitta raqam bo\'lishi kerak')
        else:
            strength_score += 1
        
        # Maxsus belgi
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append('Parolda kamida bitta maxsus belgi bo\'lishi kerak (!@#$%^&* va boshqalar)')
        else:
            strength_score += 1
        
        # Strength aniqlash
        if strength_score <= 2:
            strength = 'weak'
        elif strength_score <= 3:
            strength = 'medium'
        elif strength_score <= 4:
            strength = 'strong'
        else:
            strength = 'very_strong'
        
        valid = len(issues) == 0
        message = 'Parol to\'g\'ri' if valid else '; '.join(issues)
        
        return {
            'valid': valid,
            'message': message,
            'strength': strength
        }
    
    @staticmethod
    def validate_full_name(full_name: str) -> Dict[str, Any]:
        """
        To'liq ism validatsiyasi
        
        Returns:
            Dict: {'valid': bool, 'message': str}
        """
        if not full_name or not full_name.strip():
            return {
                'valid': False,
                'message': 'To\'liq ism kiritilmagan'
            }
        
        name = full_name.strip()
        
        # Minimum uzunlik
        if len(name) < 2:
            return {
                'valid': False,
                'message': 'Ism kamida 2 ta belgidan iborat bo\'lishi kerak'
            }
        
        # Maksimum uzunlik
        if len(name) > 100:
            return {
                'valid': False,
                'message': 'Ism 100 ta belgidan ko\'p bo\'lmasligi kerak'
            }
        
        # Faqat harflar, bo'sh joy va ba'zi maxsus belgilar
        if not re.match(r'^[a-zA-ZäöüßÄÖÜа-яёА-ЯЁ\'\-\s\.]+$', name):
            return {
                'valid': False,
                'message': 'Ismda faqat harflar, bo\'sh joy va \'-\' belgisi bo\'lishi mumkin'
            }
        
        return {
            'valid': True,
            'message': 'To\'liq ism to\'g\'ri'
        }
    
    @staticmethod
    def validate_business_name(business_name: str) -> Dict[str, Any]:
        """
        Biznes nomi validatsiyasi
        
        Returns:
            Dict: {'valid': bool, 'message': str}
        """
        if not business_name or not business_name.strip():
            return {
                'valid': False,
                'message': 'Biznes nomi kiritilmagan'
            }
        
        name = business_name.strip()
        
        # Minimum uzunlik
        if len(name) < 2:
            return {
                'valid': False,
                'message': 'Biznes nomi kamida 2 ta belgidan iborat bo\'lishi kerak'
            }
        
        # Maksimum uzunlik
        if len(name) > 200:
            return {
                'valid': False,
                'message': 'Biznes nomi 200 ta belgidan ko\'p bo\'lmasligi kerak'
            }
        
        return {
            'valid': True,
            'message': 'Biznes nomi to\'g\'ri'
        }
    
    @staticmethod
    def validate_api_key(api_key: str, provider: str) -> Dict[str, Any]:
        """
        API kalit validatsiyasi
        
        Args:
            api_key: API kalit
            provider: Provider nomi (openai, telegram, etc.)
            
        Returns:
            Dict: {'valid': bool, 'message': str}
        """
        if not api_key or not api_key.strip():
            return {
                'valid': False,
                'message': 'API kalit kiritilmagan'
            }
        
        api_key = api_key.strip()
        
        # Provider bo'yicha validatsiya
        if provider == 'openai':
            # OpenAI API kalitlari odatda sk- bilan boshlanadi
            if not api_key.startswith('sk-'):
                return {
                    'valid': False,
                    'message': 'OpenAI API kalit sk- bilan boshlanishi kerak'
                }
            
            if len(api_key) < 20:
                return {
                    'valid': False,
                    'message': 'OpenAI API kalit juda qisqa'
                }
        
        elif provider == 'telegram':
            # Telegram bot tokenlari odatda raqam:string formatda
            if not re.match(r'^[0-9]+:[a-zA-Z0-9_-]+$', api_key):
                return {
                    'valid': False,
                    'message': 'Telegram bot token formati noto\'g\'ri. Format: 123456789:ABC-DEF...'
                }
        
        return {
            'valid': True,
            'message': 'API kalit formati to\'g\'ri'
        }