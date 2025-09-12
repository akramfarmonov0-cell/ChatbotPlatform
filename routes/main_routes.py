from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename
from models.user import db, User
from utils.ai_handler import get_ai_response
import os
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.is_approved:
                login_user(user)
                return redirect(url_for('main.chat'))
            else:
                return redirect(url_for('main.pending'))
        else:
            flash('Noto\'g\'ri foydalanuvchi nomi yoki parol.')
    
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Bu foydalanuvchi nomi band.')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Bu email manzil allaqachon ro\'yxatdan o\'tgan.')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Note: Admin users must be created manually for security
        
        db.session.add(user)
        db.session.commit()
        
        flash('Ro\'yxatdan o\'tish muvaffaqiyatli! Admin tasdig\'ini kuting.')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main_bp.route('/chat')
@login_required
def chat():
    if not current_user.is_approved:
        return redirect(url_for('main.pending'))
    
    # Check trial period
    if not current_user.is_trial_active():
        flash('Trial muddatingiz tugagan. Admin bilan bog\'laning.')
        return redirect(url_for('main.home'))
    
    return render_template('chat.html')

@main_bp.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    if not current_user.is_approved:
        return jsonify({'error': 'Ruxsat yo\'q'}), 403
    
    # Check trial period
    if not current_user.is_trial_active():
        return jsonify({'error': 'Trial muddatingiz tugagan'}), 403
        
    user_input = request.json.get('message', '').strip()
    if not user_input:
        return jsonify({'reply': "Xabar bo'sh bo'lmasligi kerak."})

    # Get chat history from session
    history = session.get('chat_history', [])
    context = "\n".join([f"Foydalanuvchi: {h['user']}\nAI: {h['bot']}" for h in history[-3:]]) if history else ""

    reply = get_ai_response(user_input, context)
    
    # Update chat history
    history.append({"user": user_input, "bot": reply})
    session['chat_history'] = history[-10:]  # Keep last 10 messages

    return jsonify({'reply': reply})

@main_bp.route('/chat/history')
@login_required
def get_chat_history():
    history = session.get('chat_history', [])
    return jsonify(history)

@main_bp.route('/knowledge', methods=['GET', 'POST'])
@login_required
def knowledge():
    if not current_user.is_approved:
        return redirect(url_for('main.pending'))
    
    # Check trial period
    if not current_user.is_trial_active():
        flash('Trial muddatingiz tugagan. Admin bilan bog\'laning.')
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        file = request.files.get('file')
        
        # Ensure upload directory exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        if text:
            filename = f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            flash("Matn muvaffaqiyatli saqlandi.")

        elif file and file.filename:
            # Security: Only allow text files
            allowed_extensions = {'.txt'}
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                flash("Faqat .txt fayllar qabul qilinadi.")
                return redirect(url_for('main.knowledge'))
            
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            flash("Fayl muvaffaqiyatli yuklandi.")

        return redirect(url_for('main.knowledge'))

    # Get list of uploaded files
    files = []
    if os.path.exists(current_app.config['UPLOAD_FOLDER']):
        for f in os.listdir(current_app.config['UPLOAD_FOLDER']):
            if f.endswith(('.txt', '.pdf')):
                files.append(f)
    
    return render_template('knowledge.html', files=files)

@main_bp.route('/pending')
@login_required
def pending():
    if current_user.is_approved:
        return redirect(url_for('main.chat'))
    return render_template('pending.html')

@main_bp.route('/bots')
@login_required
def bots():
    """Bot integrations management page"""
    if not current_user.is_approved:
        return redirect(url_for('main.pending'))
    
    return render_template('user/bots.html')