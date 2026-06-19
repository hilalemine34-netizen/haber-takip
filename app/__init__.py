"""Flask uygulama fabrikası."""

import os

from dotenv import load_dotenv
from flask import Flask


def create_app() -> Flask:
    """Flask uygulamasını oluşturur ve yapılandırır.

    Returns:
        Yapılandırılmış Flask uygulama örneği.
    """
    load_dotenv()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )
    app.config["NEWS_API_KEY"] = os.getenv("NEWS_API_KEY")
    app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

    from app.routes import news_bp
    from controllers.web_controller import init_web_routes

    app.register_blueprint(news_bp)
    init_web_routes(app)

    return app
