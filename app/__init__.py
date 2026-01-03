from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from config import Config
from extensions import logger
from datetime import datetime
from flask_mail import Mail
from flask import session


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True
    
    # 🔐 MAKE SESSION PERMANENT (LOGIN + CART)
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    db.init_app(app)
    mail.init_app(app) 
    bcrypt.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)


    with app.app_context():
        from app.models import User
        try:
            db.create_all()
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            logger.info(f"Exception occurred: {e}")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_year():
        return {"current_year": datetime.utcnow().year}

    @app.context_processor
    def inject_site_settings():
        from app.models import SiteSettings
        settings = SiteSettings.query.first()
        return {"site_settings": settings}
    
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    
    return app
