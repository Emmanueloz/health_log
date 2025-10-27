# api_routes.py

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from datetime import datetime, timezone
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

# Importas limiter porque este blueprint sí lo usa
from .. import db, limiter 
from ..models.models import User, TokenBlocklist

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Faltan email o contraseña"}), 400
    
    if len(password) < 8:
        return jsonify({"msg": "La contraseña debe tener al menos 8 caracteres"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "El email ya está registrado"}), 409

    new_user = User(email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "Usuario registrado exitosamente"}), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return jsonify(access_token=access_token, refresh_token=refresh_token)

    return jsonify({"msg": "Credenciales inválidas"}), 401

@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()
    return jsonify(msg="Logout exitoso. El token ha sido invalidado.")

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify(access_token=new_access_token)

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(id=user.id, email=user.email)

@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per hour")
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()

    if user:
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(email, salt='password-reset-salt')
        # Aquí se enviaría el email con el link de reseteo
        print(f"DEBUG: Token para {email}: {token}")

    return jsonify({"msg": "Si tu email está en nuestra base de datos, recibirás un link para reestablecer tu contraseña."}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({"msg": "Faltan el token o la nueva contraseña"}), 400
    
    if len(new_password) < 8:
        return jsonify({"msg": "La contraseña debe tener al menos 8 caracteres"}), 400

    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        return jsonify({"msg": "El token ha expirado"}), 400
    except BadTimeSignature:
        return jsonify({"msg": "Token inválido"}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        user.set_password(new_password)
        db.session.commit()
        return jsonify({"msg": "Contraseña actualizada exitosamente."}), 200
    
    return jsonify({"msg": "Usuario no encontrado"}), 404