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

    app = Flask(__name__)
    app.config["NEWS_API_KEY"] = os.getenv("NEWS_API_KEY")

    from app.routes import news_bp

    app.register_blueprint(news_bp)

    return app
