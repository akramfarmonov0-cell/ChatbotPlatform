from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models.user import db, User
import secrets

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Admin huquqi kerak.')
        return redirect(url_for('main.home'))

@admin_bp.route('/')
def dashboard():
    users = User.query.all()
    # Generate a simple token for security
    if 'admin_token' not in session:
        session['admin_token'] = secrets.token_urlsafe(32)
    return render_template('admin/dashboard.html', users=users, admin_token=session['admin_token'])

@admin_bp.route('/approve/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    # Simple token verification
    if request.form.get('admin_token') != session.get('admin_token'):
        flash('Noto\'g\'ri so\'rov!')
        return redirect(url_for('admin.dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f"{user.username} tasdiqlandi!")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Simple token verification
    if request.form.get('admin_token') != session.get('admin_token'):
        flash('Noto\'g\'ri so\'rov!')
        return redirect(url_for('admin.dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("Adminni o'chirib bo'lmaydi!")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"{user.username} o'chirildi.")
    return redirect(url_for('admin.dashboard'))