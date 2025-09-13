#!/usr/bin/env python3
"""
Database initialization script
Production va development uchun boshlang'ich ma'lumotlarni yaratish
"""
import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import uuid

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Database'ni boshlang'ich ma'lumotlar bilan to'ldirish"""
    try:
        from app import create_app
        from models.user import User, db
        from models.system_stats import SystemStats
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Database initialization started...")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Check if admin user exists
            admin_user = User.query.filter_by(phone='+998901234567').first()
            
            if not admin_user:
                print("👤 Creating admin user...")
                
                # Create admin user
                admin_user = User(
                    id=str(uuid.uuid4()),
                    full_name='Admin User',
                    phone='+998901234567',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True,
                    is_active=True,
                    is_trial=False,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(admin_user)
                print("✅ Admin user created: +998901234567 / admin123")
            else:
                print("ℹ️ Admin user already exists")
            
            # Check if test user exists (for development)
            test_user = User.query.filter_by(phone='+998986558747').first()
            
            if not test_user:
                print("👤 Creating test user...")
                
                # Create test user
                test_user = User(
                    id=str(uuid.uuid4()),
                    full_name='Test User',
                    phone='+998986558747',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=False,
                    is_active=True,
                    is_trial=True,
                    trial_end_date=datetime.utcnow() + timedelta(days=30),
                    created_at=datetime.utcnow()
                )
                
                db.session.add(test_user)
                print("✅ Test user created: +998986558747 / admin123")
            else:
                print("ℹ️ Test user already exists")
            
            # Initialize system stats
            stats = SystemStats.query.first()
            if not stats:
                print("📊 Creating system stats...")
                
                stats = SystemStats(
                    total_users=0,
                    total_messages=0,
                    total_bots=0,
                    total_conversations=0
                )
                
                db.session.add(stats)
                print("✅ System stats initialized")
            else:
                print("ℹ️ System stats already exist")
            
            # Commit all changes
            db.session.commit()
            
            print("🎉 Database initialization completed successfully!")
            print("\n📋 Login credentials:")
            print("Admin: +998901234567 / admin123")
            print("Test:  +998986558747 / admin123")
            
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)