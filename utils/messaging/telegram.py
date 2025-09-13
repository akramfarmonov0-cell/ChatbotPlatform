import requests
import json
from flask import current_app
from models.messaging import TelegramBot, TelegramConversation
from models.user import db
from utils.ai_handler import get_ai_response
import os
import time
import threading
import logging

class TelegramHandler:
    """Handle Telegram Bot API operations"""
    
    @staticmethod
    def set_webhook(bot_token, webhook_url, secret_token=None):
        """Set webhook for Telegram bot with optional secret token"""
        try:
            api_url = f"{current_app.config['TELEGRAM_API_URL']}{bot_token}/setWebhook"
            
            data = {
                'url': webhook_url,
                'drop_pending_updates': True
            }
            
            # Add secret token for webhook verification
            if secret_token:
                data['secret_token'] = secret_token
            
            response = requests.post(api_url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('ok', False), result.get('description', 'Unknown error')
            
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def send_message(bot_token, chat_id, text, reply_to_message_id=None):
        """Send message via Telegram Bot API"""
        try:
            api_url = f"{current_app.config['TELEGRAM_API_URL']}{bot_token}/sendMessage"
            
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            if reply_to_message_id:
                data['reply_to_message_id'] = reply_to_message_id
            
            response = requests.post(api_url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('ok', False), result.get('result', {})
            
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def process_webhook_update(bot_id, update_data):
        """Process incoming webhook update from Telegram"""
        try:
            # Get bot instance
            bot = TelegramBot.query.get(bot_id)
            if not bot or not bot.is_active:
                return False, "Bot not found or inactive"
            
            # Extract message data
            message = update_data.get('message', {})
            if not message:
                return False, "No message in update"
            
            chat_id = str(message.get('chat', {}).get('id', ''))
            user_id = str(message.get('from', {}).get('id', ''))
            username = message.get('from', {}).get('username', '')
            text = message.get('text', '')
            
            if not text or not chat_id:
                return False, "Missing required message data"
            
            # Get AI response with knowledge base context
            from models.user import User
            user_obj = User.query.get(bot.user_id)
            ai_response = get_ai_response(text, user_obj)
            
            # Save conversation
            conversation = TelegramConversation(
                bot_id=bot_id,
                telegram_user_id=user_id,
                telegram_username=username,
                message_text=text,
                response_text=ai_response
            )
            db.session.add(conversation)
            
            # Send response back to Telegram
            bot_token = bot.get_token()
            success, result = TelegramHandler.send_message(
                bot_token, chat_id, ai_response, 
                reply_to_message_id=message.get('message_id')
            )
            
            if success:
                db.session.commit()
                return True, "Message processed and response sent"
            else:
                db.session.rollback()
                return False, f"Failed to send response: {result}"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing update: {str(e)}"
    
    @staticmethod
    def get_updates(bot_token, offset=0, timeout=10):
        """Get updates from Telegram using long polling"""
        try:
            api_url = f"{current_app.config['TELEGRAM_API_URL']}{bot_token}/getUpdates"
            
            data = {
                'offset': offset,
                'timeout': timeout,
                'limit': 100
            }
            
            response = requests.post(api_url, json=data, timeout=timeout + 5)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                return True, result.get('result', [])
            else:
                return False, result.get('description', 'Unknown error')
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    @staticmethod
    def validate_bot_token(bot_token):
        """Validate Telegram bot token by calling getMe API"""
        try:
            api_url = f"{current_app.config['TELEGRAM_API_URL']}{bot_token}/getMe"
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                return True, bot_info.get('username', 'Unknown')
            else:
                return False, result.get('description', 'Invalid token')
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"