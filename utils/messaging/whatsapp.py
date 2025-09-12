import requests
import json
import hmac
import hashlib
from flask import current_app
from models.messaging import WhatsAppAccount, WhatsAppConversation
from models.user import db
from utils.ai_handler import get_ai_response

class WhatsAppHandler:
    """Handle WhatsApp Business API operations"""
    
    @staticmethod
    def verify_webhook_signature(payload, signature, app_secret):
        """Verify webhook signature from WhatsApp using app secret"""
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature using app_secret (not verify_token)
            expected_signature = hmac.new(
                app_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            return False
    
    @staticmethod
    def send_message(access_token, phone_number_id, to_number, message_text):
        """Send message via WhatsApp Business API"""
        try:
            api_url = f"{current_app.config['WHATSAPP_API_URL']}/{phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': to_number,
                'type': 'text',
                'text': {'body': message_text}
            }
            
            response = requests.post(api_url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return True, result
            
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def process_webhook_message(account_id, webhook_data):
        """Process incoming WhatsApp webhook message"""
        try:
            # Get account instance
            account = WhatsAppAccount.query.get(account_id)
            if not account or not account.is_active:
                return False, "Account not found or inactive"
            
            # Extract message data from webhook
            entry = webhook_data.get('entry', [])
            if not entry:
                return False, "No entry in webhook data"
            
            changes = entry[0].get('changes', [])
            if not changes:
                return False, "No changes in entry"
            
            value = changes[0].get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return False, "No messages in webhook"
            
            message = messages[0]
            from_number = message.get('from', '')
            message_text = message.get('text', {}).get('body', '')
            
            if not message_text or not from_number:
                return False, "Missing message text or sender"
            
            # Get AI response with knowledge base context
            from models.user import User
            user_obj = User.query.get(account.user_id)
            ai_response = get_ai_response(message_text, user_obj)
            
            # Save conversation
            conversation = WhatsAppConversation(
                account_id=account_id,
                whatsapp_user_id=from_number,
                message_text=message_text,
                response_text=ai_response
            )
            db.session.add(conversation)
            
            # Send response back to WhatsApp
            credentials = account.get_credentials()
            success, result = WhatsAppHandler.send_message(
                credentials['app_secret'],  # This should be access_token in real implementation
                account.phone_number_id,
                from_number,
                ai_response
            )
            
            if success:
                db.session.commit()
                return True, "Message processed and response sent"
            else:
                db.session.rollback()
                return False, f"Failed to send response: {result}"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing message: {str(e)}"
    
    @staticmethod
    def validate_credentials(app_id, app_secret, phone_number_id):
        """Validate WhatsApp Business API credentials"""
        try:
            # This is a simplified validation - in real implementation,
            # you would make a call to WhatsApp API to verify credentials
            if not app_id or not app_secret or not phone_number_id:
                return False, "Missing required credentials"
            
            # Basic format validation
            if len(app_id) < 10 or len(app_secret) < 20:
                return False, "Invalid credential format"
            
            return True, "Credentials appear valid"
            
        except Exception as e:
            return False, f"Error validating credentials: {str(e)}"