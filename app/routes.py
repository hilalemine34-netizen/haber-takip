"""Haber API route'ları."""

from flask import Blueprint, current_app, jsonify, request

from services.news_service import NewsAPIError, NewsService

news_bp = Blueprint("news", __name__)


@news_bp.route("/api/news/turkey", methods=["GET"])
def turkey_news():
    """Türkiye'den güncel haber başlıklarını döndürür."""
    api_key = current_app.config.get("NEWS_API_KEY")
    if not api_key:
        return jsonify({"error": "NewsAPI anahtarı yapılandırılmamış."}), 500

    page_size = request.args.get("page_size", default=20, type=int)
    category = request.args.get("category", default=None, type=str)

    try:
        service = NewsService(api_key=api_key)
        articles = service.get_turkey_headlines(
            category=category,
            page_size=page_size,
        )
        return jsonify({"status": "ok", "count": len(articles), "articles": articles})
    except NewsAPIError as exc:
        return jsonify({"error": str(exc)}), exc.status_code
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
