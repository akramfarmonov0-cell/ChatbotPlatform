from datetime import datetime
from models.user import db
import random
import string

class MarketingMessage(db.Model):
    """Marketing habarlar - trial foydalanuvchilarga avtomatik xabarlar"""
    __tablename__ = 'marketing_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_type = db.Column(db.String(20), default='trial_reminder')  # trial_reminder, plan_expired, welcome
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='sent')  # sent, failed, pending
    email_sent = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='marketing_messages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message_type': self.message_type,
            'subject': self.subject,
            'message': self.message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status,
            'email_sent': self.email_sent
        }
    
    @staticmethod
    def create_trial_reminder(user_id):
        """Trial eslatma xabarini yaratish"""
        subject = "Sizning sinov muddatingiz tugagan - 10% chegirma!"
        message = """
        Salom!
        
        Sizning 3 kunlik sinov muddatingiz tugagan. AI chatbot platformamizdan foydalanishni davom ettirish uchun pullik rejalardan birini tanlang.
        
        🎉 Maxsus taklifimiz: 10% chegirma!
        
        Quyidagi rejalardan birini tanlang:
        - Oylik reja: $29/oy (10% chegirma bilan $26.10)
        - Choraklik reja: $79/3 oy (10% chegirma bilan $71.10)
        - Yillik reja: $299/yil (10% chegirma bilan $269.10)
        
        Platformaga kiring va "Dostupni so'rash" tugmasini bosing.
        
        Rahmat!
        AI Chatbot Platform jamoasi
        """
        
        marketing_msg = MarketingMessage(
            user_id=user_id,
            message_type='trial_reminder',
            subject=subject,
            message=message
        )
        return marketing_msg

class Coupon(db.Model):
    """Chegirma kuponlari"""
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Integer, default=10)  # 10%
    is_active = db.Column(db.Boolean, default=True)
    usage_limit = db.Column(db.Integer, default=100)  # nechta marta ishlatish mumkin
    used_count = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    admin = db.relationship('User', backref='created_coupons')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'discount_percent': self.discount_percent,
            'is_active': self.is_active,
            'usage_limit': self.usage_limit,
            'used_count': self.used_count,
            'remaining_uses': self.usage_limit - self.used_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @staticmethod
    def generate_coupon_code():
        """Random kupon kodi yaratish"""
        # Format: SAVE10_UZ_2025_XXXX
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"SAVE10_UZ_2025_{random_suffix}"
    
    @staticmethod
    def create_new_coupon(admin_id, discount_percent=10, usage_limit=100):
        """Yangi kupon yaratish"""
        code = Coupon.generate_coupon_code()
        
        # Agar kod mavjud bo'lsa, yangi yaratish
        while Coupon.query.filter_by(code=code).first():
            code = Coupon.generate_coupon_code()
        
        coupon = Coupon(
            code=code,
            discount_percent=discount_percent,
            usage_limit=usage_limit,
            created_by=admin_id
        )
        return coupon
    
    def is_valid(self):
        """Kupon hali ham amal qiladimi tekshirish"""
        if not self.is_active:
            return False
        if self.used_count >= self.usage_limit:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def use_coupon(self):
        """Kupondan foydalanish"""
        if self.is_valid():
            self.used_count += 1
            return True
        return False

class CouponUsage(db.Model):
    """Kupon ishlatish tarixi"""
    __tablename__ = 'coupon_usages'
    
    id = db.Column(db.Integer, primary_key=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    plan_request_id = db.Column(db.Integer, db.ForeignKey('plan_requests.id'))
    
    # Relationships
    coupon = db.relationship('Coupon', backref='usages')
    user = db.relationship('User', backref='coupon_usages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'coupon_code': self.coupon.code if self.coupon else None,
            'user_id': self.user_id,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'plan_request_id': self.plan_request_id
        }