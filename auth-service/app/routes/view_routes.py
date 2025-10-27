# view_routes.py

from flask import Blueprint, request, current_app, render_template, redirect, url_for, session, flash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

# Nota: No se importa limiter, jwt, ni TokenBlocklist porque no se usan aquí
from .. import db
from ..models.models import User

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def home():
    return redirect(url_for('views.login_view'))

@views_bp.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Faltan email o contraseña', 'error')
            return render_template('auth_login.jinja2')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('views.profile_view'))
        flash('Credenciales inválidas', 'error')
    return render_template('auth_login.jinja2')

@views_bp.route('/logout', methods=['POST'])
def logout_view():
    session.pop('user_id', None)
    return redirect(url_for('views.login_view'))

@views_bp.route('/register', methods=['GET', 'POST'])
def register_view():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Faltan email o contraseña', 'error')
            return render_template('auth_register.jinja2')
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'error')
            return render_template('auth_register.jinja2')
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
            return render_template('auth_register.jinja2')
        new_user = User(email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuario registrado exitosamente. Ahora inicia sesión.', 'success')
        return redirect(url_for('views.login_view'))
    return render_template('auth_register.jinja2')

@views_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_view():
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(email, salt='password-reset-salt')
            # Lógica para enviar email iría aquí
            print(f"DEBUG (Vistas): Token para {email}: {token}")
            flash('Si tu email está registrado, te enviamos instrucciones.', 'info')
        else:
            flash('Ingresa un email válido', 'error')
    return render_template('auth_forgot_password.jinja2')

@views_bp.route('/reset-password', methods=['GET', 'POST'])
@views_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_view(token=None):
    if request.method == 'POST':
        form_token = request.form.get('token') or token
        new_password = request.form.get('new_password')
        if not form_token or not new_password:
            flash('Faltan el token o la nueva contraseña', 'error')
            return render_template('auth_reset_password.jinja2', token=token)
        if len(new_password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'error')
            return render_template('auth_reset_password.jinja2', token=token)
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(form_token, salt='password-reset-salt', max_age=3600)
        except SignatureExpired:
            flash('El token ha expirado', 'error')
            return render_template('auth_reset_password.jinja2', token=token)
        except BadTimeSignature:
            flash('Token inválido', 'error')
            return render_template('auth_reset_password.jinja2', token=token)
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            flash('Contraseña actualizada exitosamente.', 'success')
            return redirect(url_for('views.login_view'))
        flash('Usuario no encontrado', 'error')
    return render_template('auth/reset_password.html', token=token)

@views_bp.route('/profile', methods=['GET'])
def profile_view():
    user_id = session.get('user_id')
    if not user_id:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('views.login_view'))
    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        flash('Sesión inválida. Inicia sesión de nuevo.', 'error')
        return redirect(url_for('views.login_view'))
    return render_template('auth_profile.jinja2', user=user)