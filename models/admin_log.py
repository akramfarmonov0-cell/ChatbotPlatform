from datetime import datetime
from models.user import db

class AdminLog(db.Model):
    """Admin harakatlari logi"""
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # user_banned, plan_approved, coupon_created, etc.
    target_type = db.Column(db.String(50))  # user, coupon, plan_request, conversation
    target_id = db.Column(db.Integer)  # ID of the target object
    details = db.Column(db.Text)  # JSON string with additional details
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('User', backref='admin_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_name': self.admin.full_name if self.admin else 'Unknown',
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @staticmethod
    def log_action(admin_id, action, target_type=None, target_id=None, details=None, ip_address=None, user_agent=None):
        """Admin harakatini loglash"""
        log_entry = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log_entry)
        return log_entry
    
    @staticmethod
    def get_recent_logs(limit=100):
        """So'nggi admin loglarini olish"""
        return AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_admin_activity(admin_id, limit=50):
        """Muayyan admin faoliyatini olish"""
        return AdminLog.query.filter_by(admin_id=admin_id)\
                           .order_by(AdminLog.timestamp.desc())\
                           .limit(limit).all()

class SystemStats(db.Model):
    """Tizim statistikalari"""
    __tablename__ = 'system_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    stat_date = db.Column(db.Date, default=datetime.utcnow().date)
    total_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)  # so'nggi 30 kun ichida aktiv
    paid_users = db.Column(db.Integer, default=0)
    trial_users = db.Column(db.Integer, default=0)
    total_conversations = db.Column(db.Integer, default=0)
    telegram_conversations = db.Column(db.Integer, default=0)
    whatsapp_conversations = db.Column(db.Integer, default=0)
    instagram_conversations = db.Column(db.Integer, default=0)
    total_knowledge_bases = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'stat_date': self.stat_date.isoformat() if self.stat_date else None,
            'total_users': self.total_users,
            'active_users': self.active_users,
            'paid_users': self.paid_users,
            'trial_users': self.trial_users,
            'total_conversations': self.total_conversations,
            'telegram_conversations': self.telegram_conversations,
            'whatsapp_conversations': self.whatsapp_conversations,
            'instagram_conversations': self.instagram_conversations,
            'total_knowledge_bases': self.total_knowledge_bases,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def generate_daily_stats():
        """Kunlik statistikani yaratish"""
        from models.user import User
        from models.conversation import Conversation
        from models.knowledge_base import KnowledgeBase
        from sqlalchemy import func, and_
        from datetime import timedelta
        
        today = datetime.utcnow().date()
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Statistikalarni hisoblash
        total_users = User.query.count()
        active_users = User.query.filter(User.last_login >= thirty_days_ago).count()
        paid_users = User.query.filter(and_(User.plan != 'free', User.is_plan_active)).count()
        trial_users = User.query.filter(and_(User.plan == 'free', ~User.is_trial_expired)).count()
        
        total_conversations = Conversation.query.count()
        telegram_convs = Conversation.query.filter_by(platform='telegram').count()
        whatsapp_convs = Conversation.query.filter_by(platform='whatsapp').count()
        instagram_convs = Conversation.query.filter_by(platform='instagram').count()
        
        total_kb = KnowledgeBase.query.filter_by(is_active=True).count()
        
        # Statistikani saqlash
        stats = SystemStats(
            stat_date=today,
            total_users=total_users,
            active_users=active_users,
            paid_users=paid_users,
            trial_users=trial_users,
            total_conversations=total_conversations,
            telegram_conversations=telegram_convs,
            whatsapp_conversations=whatsapp_convs,
            instagram_conversations=instagram_convs,
            total_knowledge_bases=total_kb
        )
        
        db.session.add(stats)
        return stats