import requests
import json
from typing import Dict, Any, Optional
from flask import current_app
import time

class TelegramUtils:
    """Telegram bot utilitasi"""
    
    @staticmethod
    def send_message(bot_token: str, chat_id: str, message: str, 
                    parse_mode: str = "HTML") -> Dict[str, Any]:
        """
        Telegram orqali xabar yuborish
        
        Args:
            bot_token: Bot token
            chat_id: Chat ID
            message: Yuborilayotgan xabar
            parse_mode: Xabar formati (HTML, Markdown)
            
        Returns:
            Dict: {'success': bool, 'error': str, 'message_id': int}
        """
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return {
                    'success': True,
                    'error': None,
                    'message_id': result['result']['message_id']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('description', 'Noma\'lum xato'),
                    'message_id': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Telegram API xato: {str(e)}',
                'message_id': None
            }
    
    @staticmethod
    def set_webhook(bot_token: str, webhook_url: str) -> Dict[str, Any]:
        """
        Webhook o'rnatish
        
        Returns:
            Dict: {'success': bool, 'error': str}
        """
        try:
            url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            
            data = {
                'url': webhook_url
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return {
                    'success': True,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': result.get('description', 'Webhook o\'rnatishda xato')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Webhook o\'rnatishda xato: {str(e)}'
            }
    
    @staticmethod
    def get_bot_info(bot_token: str) -> Dict[str, Any]:
        """
        Bot haqida ma'lumot olish
        
        Returns:
            Dict: {'success': bool, 'error': str, 'bot_info': dict}
        """
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return {
                    'success': True,
                    'error': None,
                    'bot_info': result['result']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('description', 'Bot ma\'lumotlarini olishda xato'),
                    'bot_info': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Bot ma\'lumotlarini olishda xato: {str(e)}',
                'bot_info': None
            }

class WhatsAppUtils:
    """WhatsApp Business API utilitasi"""
    
    @staticmethod
    def send_message(app_id: str, app_secret: str, phone_number_id: str, 
                    to_number: str, message: str) -> Dict[str, Any]:
        """
        WhatsApp orqali xabar yuborish
        
        Args:
            app_id: App ID
            app_secret: App Secret
            phone_number_id: Phone Number ID
            to_number: Qabul qiluvchi raqam
            message: Xabar matni
            
        Returns:
            Dict: {'success': bool, 'error': str, 'message_id': str}
        """
        try:
            # Access token olish
            access_token = WhatsAppUtils._get_access_token(app_id, app_secret)
            if not access_token:
                return {
                    'success': False,
                    'error': 'Access token olinmadi',
                    'message_id': None
                }
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': to_number,
                'text': {'body': message}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'error': None,
                    'message_id': result.get('messages', [{}])[0].get('id')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('message', 'WhatsApp API xato'),
                    'message_id': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'WhatsApp API xato: {str(e)}',
                'message_id': None
            }
    
    @staticmethod
    def _get_access_token(app_id: str, app_secret: str) -> Optional[str]:
        """WhatsApp uchun access token olish"""
        try:
            url = f"https://graph.facebook.com/oauth/access_token"
            
            params = {
                'grant_type': 'client_credentials',
                'client_id': app_id,
                'client_secret': app_secret
            }
            
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            return result.get('access_token')
            
        except:
            return None

class MessagingUtils:
    """Umumiy messaging utilities"""
    
    def __init__(self):
        self.telegram = TelegramUtils()
        self.whatsapp = WhatsAppUtils()
        self.instagram = InstagramUtils()
    
    def send_message(self, platform: str, **kwargs) -> Dict[str, Any]:
        """Platform bo'yicha xabar yuborish"""
        if platform == 'telegram':
            return self.telegram.send_message(**kwargs)
        elif platform == 'whatsapp':
            return self.whatsapp.send_message(**kwargs)
        elif platform == 'instagram':
            return self.instagram.send_message(**kwargs)
        else:
            return {'success': False, 'error': f'Noma\'lum platform: {platform}'}

class InstagramUtils:
    """Instagram Business API utilitasi"""
    
    @staticmethod
    def send_message(access_token: str, page_id: str, recipient_id: str, 
                    message: str) -> Dict[str, Any]:
        """
        Instagram Direct orqali xabar yuborish
        
        Args:
            access_token: Access token
            page_id: Page ID
            recipient_id: Qabul qiluvchi ID
            message: Xabar matni
            
        Returns:
            Dict: {'success': bool, 'error': str, 'message_id': str}
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{page_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'recipient': {'id': recipient_id},
                'message': {'text': message}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'error': None,
                    'message_id': result.get('message_id')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('message', 'Instagram API xato'),
                    'message_id': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Instagram API xato: {str(e)}',
                'message_id': None
            }
    
    @staticmethod
    def reply_to_comment(access_token: str, comment_id: str, 
                        message: str) -> Dict[str, Any]:
        """
        Instagram komentga javob berish
        
        Args:
            access_token: Access token
            comment_id: Koment ID
            message: Javob matni
            
        Returns:
            Dict: {'success': bool, 'error': str, 'comment_id': str}
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{comment_id}/replies"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'message': message
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'error': None,
                    'comment_id': result.get('id')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('message', 'Instagram API xato'),
                    'comment_id': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Instagram API xato: {str(e)}',
                'comment_id': None
            }

class MessagingManager:
    """Barcha messaging platformalar uchun umumiy manager"""
    
    @staticmethod
    def send_ai_response(platform: str, credentials: dict, recipient: str, 
                        ai_response: str) -> Dict[str, Any]:
        """
        AI javobini yuborish
        
        Args:
            platform: telegram, whatsapp, instagram
            credentials: Platform uchun kerakli ma'lumotlar
            recipient: Qabul qiluvchi
            ai_response: AI javobi
            
        Returns:
            Dict: {'success': bool, 'error': str, 'message_id': str}
        """
        try:
            if platform == 'telegram':
                return TelegramUtils.send_message(
                    credentials['token'],
                    recipient,
                    ai_response
                )
            
            elif platform == 'whatsapp':
                return WhatsAppUtils.send_message(
                    credentials['app_id'],
                    credentials['app_secret'],
                    credentials['phone_number_id'],
                    recipient,
                    ai_response
                )
            
            elif platform == 'instagram':
                return InstagramUtils.send_message(
                    credentials['access_token'],
                    credentials['page_id'],
                    recipient,
                    ai_response
                )
            
            else:
                return {
                    'success': False,
                    'error': f'Noma\'lum platform: {platform}',
                    'message_id': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Xabar yuborishda xato: {str(e)}',
                'message_id': None
            }