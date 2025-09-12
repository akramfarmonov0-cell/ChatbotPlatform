# Import all models to ensure they are registered with SQLAlchemy
from models.user import db, User
from models.admin_log import AdminLog, SystemStats
from models.ai_config import AIConfig
from models.conversation import Conversation, Message
from models.knowledge_base import KnowledgeBase
from models.marketing import MarketingMessage, Coupon
from models.messaging import (
    MessagingPlatform, PlatformCredentials, TelegramBot, 
    WhatsAppAccount, InstagramAccount, TelegramConversation, 
    WhatsAppConversation, InstagramConversation, PlanRequest
)

# Export all models and db instance
__all__ = [
    'db', 'User', 'AdminLog', 'SystemStats', 'AIConfig', 
    'Conversation', 'Message', 'KnowledgeBase', 'MarketingMessage', 
    'Coupon', 'MessagingPlatform', 'PlatformCredentials', 'TelegramBot',
    'WhatsAppAccount', 'InstagramAccount', 'TelegramConversation',
    'WhatsAppConversation', 'InstagramConversation', 'PlanRequest'
]