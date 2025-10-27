# __init__.py

import os
from datetime import timedelta, datetime, timezone
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# Instanciar las extensiones
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
    
def create_app():
    """
    Fábrica de la aplicación Flask.
    """
    app = Flask(__name__)

    # Cargar configuración
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("AUTH_DB_URL") or os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("AUTH_SERVICE_SECRET_KEY") or app.config["SECRET_KEY"]
    
    # Hardening: Configuración de expiración para los tokens
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    # Vincular extensiones a la aplicación
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # Importar modelos para que Alembic (Migrate) los detecte
    from . import models
    with app.app_context():
        db.create_all()

    # Callback para verificar si un token ha sido revocado (logout forzado)
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token = db.session.query(models.TokenBlocklist.id).filter_by(jti=jti).scalar()
        return token is not None

    # Registrar el Blueprint con las rutas
    from .routes.auth_routes import auth_bp
    from .routes.view_routes import views_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth") # La API
    app.register_blueprint(views_bp, url_prefix="/")

    return app