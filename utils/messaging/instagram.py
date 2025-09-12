import requests
import json
from flask import current_app
from models.messaging import InstagramAccount, InstagramConversation
from models.user import db
from utils.ai_handler import get_ai_response

class InstagramHandler:
    """Handle Instagram Graph API operations"""
    
    @staticmethod
    def validate_access_token(access_token, page_id):
        """Validate Instagram access token and page ID"""
        try:
            api_url = f"{current_app.config['INSTAGRAM_API_URL']}/{page_id}"
            
            params = {
                'fields': 'id,name,username',
                'access_token': access_token
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if 'id' in result:
                return True, result.get('username', 'Unknown')
            else:
                return False, "Invalid access token or page ID"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def reply_to_comment(access_token, comment_id, message_text):
        """Reply to Instagram comment"""
        try:
            api_url = f"{current_app.config['INSTAGRAM_API_URL']}/{comment_id}/replies"
            
            data = {
                'message': message_text,
                'access_token': access_token
            }
            
            response = requests.post(api_url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return True, result
            
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def send_direct_message(access_token, page_id, recipient_id, message_text):
        """Send direct message via Instagram"""
        try:
            api_url = f"{current_app.config['INSTAGRAM_API_URL']}/{page_id}/messages"
            
            data = {
                'recipient': {'id': recipient_id},
                'message': {'text': message_text},
                'access_token': access_token
            }
            
            response = requests.post(api_url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return True, result
            
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def process_webhook_update(account_id, webhook_data):
        """Process incoming Instagram webhook update"""
        try:
            # Get account instance
            account = InstagramAccount.query.get(account_id)
            if not account or not account.is_active:
                return False, "Account not found or inactive"
            
            # Extract data from webhook
            entry = webhook_data.get('entry', [])
            if not entry:
                return False, "No entry in webhook data"
            
            changes = entry[0].get('changes', [])
            if not changes:
                return False, "No changes in entry"
            
            value = changes[0].get('value', {})
            
            # Handle different types of updates (comments, messages)
            if 'comment_id' in value:
                return InstagramHandler._process_comment(account, value)
            elif 'message' in value:
                return InstagramHandler._process_direct_message(account, value)
            else:
                return False, "Unknown webhook update type"
                
        except Exception as e:
            return False, f"Error processing update: {str(e)}"
    
    @staticmethod
    def _process_comment(account, comment_data):
        """Process Instagram comment"""
        try:
            comment_id = comment_data.get('comment_id', '')
            text = comment_data.get('text', '')
            from_user = comment_data.get('from', {})
            user_id = str(from_user.get('id', ''))
            username = from_user.get('username', '')
            
            if not text or not user_id:
                return False, "Missing comment data"
            
            # Get AI response with knowledge base context
            from models.user import User
            user_obj = User.query.get(account.user_id)
            ai_response = get_ai_response(text, user_obj)
            
            # Save conversation
            conversation = InstagramConversation(
                account_id=account.id,
                instagram_user_id=user_id,
                instagram_username=username,
                message_text=text,
                response_text=ai_response,
                message_type='comment'
            )
            db.session.add(conversation)
            
            # Reply to comment
            access_token = account.get_access_token()
            success, result = InstagramHandler.reply_to_comment(
                access_token, comment_id, ai_response
            )
            
            if success:
                db.session.commit()
                return True, "Comment processed and reply sent"
            else:
                db.session.rollback()
                return False, f"Failed to send reply: {result}"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing comment: {str(e)}"
    
    @staticmethod
    def _process_direct_message(account, message_data):
        """Process Instagram direct message"""
        try:
            message = message_data.get('message', {})
            text = message.get('text', '')
            sender = message_data.get('sender', {})
            user_id = str(sender.get('id', ''))
            
            if not text or not user_id:
                return False, "Missing message data"
            
            # Get AI response with knowledge base context
            from models.user import User
            user_obj = User.query.get(account.user_id)
            ai_response = get_ai_response(text, user_obj)
            
            # Save conversation
            conversation = InstagramConversation(
                account_id=account.id,
                instagram_user_id=user_id,
                message_text=text,
                response_text=ai_response,
                message_type='direct_message'
            )
            db.session.add(conversation)
            
            # Send direct message reply
            access_token = account.get_access_token()
            success, result = InstagramHandler.send_direct_message(
                access_token, account.page_id, user_id, ai_response
            )
            
            if success:
                db.session.commit()
                return True, "Message processed and reply sent"
            else:
                db.session.rollback()
                return False, f"Failed to send reply: {result}"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing message: {str(e)}"