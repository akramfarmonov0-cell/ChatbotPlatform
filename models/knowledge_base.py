from datetime import datetime
from models.user import db

class KnowledgeBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # uploads/knowledge/user_id/filename
    content = db.Column(db.Text, nullable=False)  # faqat matn — PDF/DOCX dan olingan
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    file_type = db.Column(db.String(10), nullable=False)  # pdf, docx, csv, txt
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_active': self.is_active,
            'content_preview': self.content[:200] + '...' if len(self.content) > 200 else self.content
        }
    
    @staticmethod
    def get_allowed_extensions():
        return {'pdf', 'docx', 'csv', 'txt'}
    
    @staticmethod
    def is_allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in KnowledgeBase.get_allowed_extensions()