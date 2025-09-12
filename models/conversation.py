from datetime import datetime
from models.user import db

class Message(db.Model):
    """Suhbat xabarlari modeli"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)
    metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = db.relationship('Conversation', backref='messages')

class Conversation(db.Model):
    """Barcha platformalar uchun umumiy suhbat modeli"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False)  # telegram, whatsapp, instagram
    sender_id = db.Column(db.String(100), nullable=False)  # mijoz ID
    sender_name = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    reply = db.Column(db.Text)
    language = db.Column(db.String(2))  # uz, ru, en
    message_type = db.Column(db.String(20), default='text')  # text, image, document, etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_time = db.Column(db.Float)  # seconds
    ai_provider = db.Column(db.String(20), default='gemini')  # gemini, openai
    
    # Relationships
    user = db.relationship('User', backref='conversations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'message': self.message,
            'reply': self.reply,
            'language': self.language,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'response_time': self.response_time,
            'ai_provider': self.ai_provider
        }
    
    @staticmethod
    def get_platform_stats(user_id):
        """Platform statistikalarini olish"""
        from sqlalchemy import func
        stats = db.session.query(
            Conversation.platform,
            func.count(Conversation.id).label('count')
        ).filter_by(user_id=user_id).group_by(Conversation.platform).all()
        
        return {platform: count for platform, count in stats}
    
    @staticmethod
    def get_recent_conversations(user_id, limit=50):
        """So'nggi suhbatlarni olish"""
        return Conversation.query.filter_by(user_id=user_id)\
                                .order_by(Conversation.timestamp.desc())\
                                .limit(limit).all()