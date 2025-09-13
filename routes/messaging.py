from flask import Blueprint, request, jsonify, current_app, session, redirect, url_for, render_template
from flask_login import current_user
from models.messaging import TelegramBot, WhatsAppAccount, InstagramAccount
from models.user import User, db
from utils.messaging.telegram import TelegramHandler
from utils.messaging.whatsapp import WhatsAppHandler
from utils.messaging.instagram import InstagramHandler
from functools import wraps
import logging

messaging_bp = Blueprint('messaging', __name__, url_prefix='/')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def login_required(f):
    """Login talab qiluvchi decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Tizimga kirish talab qilinadi'}), 401
            return redirect(url_for('auth.login'))
        
        # Foydalanuvchi mavjudligini tekshirish
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            if request.is_json:
                return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'}), 401
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

# ===== MAIN REDIRECT ROUTE =====

@messaging_bp.route('/messaging')
@login_required
def messaging_redirect():
    """Messaging sahifasidan dashboard/platforms ga yo'naltirish"""
    return redirect(url_for('dashboard.messaging_platforms'))

# ===== TELEGRAM WEBHOOK ROUTES =====

@messaging_bp.route('/telegram/webhook/<int:user_id>', methods=['POST'])
def telegram_webhook(user_id):
    """Handle incoming Telegram webhook updates"""
    try:
        # Get JSON data from request
        update_data = request.get_json()
        if not update_data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Find active bot for this user
        bot = TelegramBot.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).first()
        
        if not bot:
            logger.warning(f"No active Telegram bot found for user {user_id}")
            return jsonify({'error': 'Bot not found or inactive'}), 404
        
        # Process the update
        success, message = TelegramHandler.process_webhook_update(bot.id, update_data)
        
        if success:
            logger.info(f"Telegram webhook processed successfully for bot {bot.id}")
            return jsonify({'status': 'success', 'message': message}), 200
        else:
            logger.error(f"Telegram webhook processing failed: {message}")
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"Telegram webhook error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@messaging_bp.route('/telegram/set-webhook', methods=['POST'])
@login_required
def set_telegram_webhook():
    """Set webhook for user's Telegram bot"""
    try:
        # Check if user is approved
        if not current_user.is_approved:
            return jsonify({'error': 'User not approved for bot integrations'}), 403
        
        # Check if running on Replit
        if current_app.config.get('IS_REPLIT', False):
            return jsonify({
                'error': 'Webhook setup not available on Replit. Deploy to production (Render/Railway) to enable this feature.'
            }), 400
        
        data = request.get_json()
        bot_id = data.get('bot_id')
        
        if not bot_id:
            return jsonify({'error': 'Bot ID required'}), 400
        
        # Get user's bot
        bot = TelegramBot.query.filter_by(
            id=bot_id,
            user_id=current_user.id
        ).first()
        
        if not bot:
            return jsonify({'error': 'Bot not found'}), 404
        
        # Generate webhook URL
        webhook_url = f"{current_app.config['WEBHOOK_BASE_URL']}/telegram/webhook/{current_user.id}"
        
        # Set webhook via Telegram API
        bot_token = bot.get_token()
        success, message = TelegramHandler.set_webhook(bot_token, webhook_url)
        
        if success:
            # Update bot record
            bot.webhook_url = webhook_url
            bot.is_active = True
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Webhook set successfully',
                'webhook_url': webhook_url
            }), 200
        else:
            return jsonify({'error': f'Failed to set webhook: {message}'}), 400
            
    except Exception as e:
        logger.error(f"Set Telegram webhook error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# ===== WHATSAPP WEBHOOK ROUTES =====

@messaging_bp.route('/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Handle WhatsApp Business API webhooks"""
    
    if request.method == 'GET':
        # Webhook verification (challenge)
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # Find account with this verify token
        # Note: In production, you should have a more secure way to handle this
        if mode == 'subscribe' and token and challenge:
            # For simplicity, we'll return the challenge
            # In production, verify against stored verify_token
            return challenge, 200
        
        return 'Verification failed', 403
    
    else:  # POST request
        try:
            webhook_data = request.get_json()
            if not webhook_data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Extract phone number ID to find the account
            entry = webhook_data.get('entry', [])
            if not entry:
                return jsonify({'error': 'No entry in webhook data'}), 400
            
            changes = entry[0].get('changes', [])
            if not changes:
                return jsonify({'error': 'No changes in entry'}), 400
            
            value = changes[0].get('value', {})
            metadata = value.get('metadata', {})
            phone_number_id = metadata.get('phone_number_id', '')
            
            if not phone_number_id:
                return jsonify({'error': 'No phone number ID found'}), 400
            
            # Find account by phone number ID
            account = WhatsAppAccount.query.filter_by(
                phone_number_id=phone_number_id,
                is_active=True
            ).first()
            
            if not account:
                logger.warning(f"No active WhatsApp account found for phone number {phone_number_id}")
                return jsonify({'error': 'Account not found or inactive'}), 404
            
            # Process the message
            success, message = WhatsAppHandler.process_webhook_message(account.id, webhook_data)
            
            if success:
                logger.info(f"WhatsApp webhook processed successfully for account {account.id}")
                return jsonify({'status': 'success'}), 200
            else:
                logger.error(f"WhatsApp webhook processing failed: {message}")
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

# ===== INSTAGRAM WEBHOOK ROUTES =====

@messaging_bp.route('/instagram/webhook', methods=['GET', 'POST'])
def instagram_webhook():
    """Handle Instagram Graph API webhooks"""
    
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token and challenge:
            # In production, verify the token against stored values
            return challenge, 200
        
        return 'Verification failed', 403
    
    else:  # POST request
        try:
            webhook_data = request.get_json()
            if not webhook_data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Extract page ID to find the account
            entry = webhook_data.get('entry', [])
            if not entry:
                return jsonify({'error': 'No entry in webhook data'}), 400
            
            page_id = entry[0].get('id', '')
            if not page_id:
                return jsonify({'error': 'No page ID found'}), 400
            
            # Find account by page ID
            account = InstagramAccount.query.filter_by(
                page_id=page_id,
                is_active=True
            ).first()
            
            if not account:
                logger.warning(f"No active Instagram account found for page {page_id}")
                return jsonify({'error': 'Account not found or inactive'}), 404
            
            # Process the update
            success, message = InstagramHandler.process_webhook_update(account.id, webhook_data)
            
            if success:
                logger.info(f"Instagram webhook processed successfully for account {account.id}")
                return jsonify({'status': 'success'}), 200
            else:
                logger.error(f"Instagram webhook processing failed: {message}")
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"Instagram webhook error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

# ===== BOT MANAGEMENT ROUTES =====

@messaging_bp.route('/api/bots/telegram/validate', methods=['POST'])
@login_required
def validate_telegram_bot():
    """Validate Telegram bot token"""
    try:
        data = request.get_json()
        bot_token = data.get('bot_token', '')
        
        if not bot_token:
            return jsonify({'error': 'Bot token required'}), 400
        
        success, result = TelegramHandler.validate_bot_token(bot_token)
        
        if success:
            return jsonify({
                'valid': True,
                'bot_username': result
            }), 200
        else:
            return jsonify({
                'valid': False,
                'error': result
            }), 400
            
    except Exception as e:
        return jsonify({'error': 'Validation failed'}), 500

@messaging_bp.route('/api/bots/whatsapp/validate', methods=['POST'])
@login_required
def validate_whatsapp_credentials():
    """Validate WhatsApp Business API credentials"""
    try:
        data = request.get_json()
        app_id = data.get('app_id', '')
        app_secret = data.get('app_secret', '')
        phone_number_id = data.get('phone_number_id', '')
        
        success, result = WhatsAppHandler.validate_credentials(app_id, app_secret, phone_number_id)
        
        if success:
            return jsonify({'valid': True, 'message': result}), 200
        else:
            return jsonify({'valid': False, 'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': 'Validation failed'}), 500

@messaging_bp.route('/api/bots/instagram/validate', methods=['POST'])
@login_required
def validate_instagram_credentials():
    """Validate Instagram access token and page ID"""
    try:
        data = request.get_json()
        access_token = data.get('access_token', '')
        page_id = data.get('page_id', '')
        
        success, result = InstagramHandler.validate_access_token(access_token, page_id)
        
        if success:
            return jsonify({
                'valid': True,
                'account_username': result
            }), 200
        else:
            return jsonify({
                'valid': False,
                'error': result
            }), 400
            
    except Exception as e:
        return jsonify({'error': 'Validation failed'}), 500

# ===== BOT SAVE ENDPOINTS =====

@messaging_bp.route('/api/bots/telegram/save', methods=['POST'])
@login_required
def save_telegram_bot():
    """Save Telegram bot configuration"""
    try:
        data = request.get_json()
        bot_name = data.get('bot_name', '')
        bot_token = data.get('bot_token', '')
        
        if not bot_name or not bot_token:
            return jsonify({'error': 'Bot name and token required'}), 400
        
        # Get current user from session
        user = User.query.get(session['user_id'])
        
        # Create new bot
        bot = TelegramBot(
            user_id=user.id,
            bot_name=bot_name
        )
        bot.set_token(bot_token)
        
        db.session.add(bot)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Bot saved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Save Telegram bot error: {str(e)}")
        return jsonify({'error': 'Failed to save bot'}), 500

@messaging_bp.route('/api/bots/whatsapp/save', methods=['POST'])
@login_required
def save_whatsapp_account():
    """Save WhatsApp Business account configuration"""
    try:
        data = request.get_json()
        business_name = data.get('business_name', '')
        app_id = data.get('app_id', '')
        app_secret = data.get('app_secret', '')
        verify_token = data.get('verify_token', '')
        phone_number_id = data.get('phone_number_id', '')
        
        if not all([business_name, app_id, app_secret, verify_token, phone_number_id]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Get current user from session
        user = User.query.get(session['user_id'])
        
        # Create new account
        account = WhatsAppAccount(
            user_id=user.id,
            business_name=business_name,
            phone_number_id=phone_number_id
        )
        account.set_credentials(app_id, app_secret, verify_token)
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Account saved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Save WhatsApp account error: {str(e)}")
        return jsonify({'error': 'Failed to save account'}), 500

@messaging_bp.route('/api/bots/instagram/save', methods=['POST'])
@login_required
def save_instagram_account():
    """Save Instagram Business account configuration"""
    try:
        data = request.get_json()
        account_name = data.get('account_name', '')
        access_token = data.get('access_token', '')
        page_id = data.get('page_id', '')
        
        if not all([account_name, access_token, page_id]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Get current user from session
        user = User.query.get(session['user_id'])
        
        # Create new account
        account = InstagramAccount(
            user_id=user.id,
            account_name=account_name,
            page_id=page_id
        )
        account.set_access_token(access_token)
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Account saved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Save Instagram account error: {str(e)}")
        return jsonify({'error': 'Failed to save account'}), 500

# ===== BOT DELETE ENDPOINTS =====

@messaging_bp.route('/api/bots/telegram/<int:bot_id>', methods=['DELETE'])
@login_required
def delete_telegram_bot(bot_id):
    """Delete Telegram bot"""
    try:
        bot = TelegramBot.query.filter_by(
            id=bot_id,
            user_id=current_user.id
        ).first()
        
        if not bot:
            return jsonify({'error': 'Bot not found'}), 404
        
        db.session.delete(bot)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Bot deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete Telegram bot error: {str(e)}")
        return jsonify({'error': 'Failed to delete bot'}), 500

@messaging_bp.route('/api/bots/whatsapp/<int:account_id>', methods=['DELETE'])
@login_required
def delete_whatsapp_account(account_id):
    """Delete WhatsApp Business account"""
    try:
        account = WhatsAppAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id
        ).first()
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete WhatsApp account error: {str(e)}")
        return jsonify({'error': 'Failed to delete account'}), 500

@messaging_bp.route('/api/bots/instagram/<int:account_id>', methods=['DELETE'])
@login_required
def delete_instagram_account(account_id):
    """Delete Instagram Business account"""
    try:
        account = InstagramAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id
        ).first()
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete Instagram account error: {str(e)}")
        return jsonify({'error': 'Failed to delete account'}), 500