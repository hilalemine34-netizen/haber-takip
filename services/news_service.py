"""NewsAPI ile haber çekme servisi."""

from typing import Any

import requests

NEWS_API_BASE_URL = "https://newsapi.org/v2/top-headlines"
DEFAULT_TIMEOUT = 10


class NewsAPIError(Exception):
    """NewsAPI kaynaklı hataları temsil eder."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        """Hata mesajı ve HTTP durum kodunu kaydeder."""
        super().__init__(message)
        self.status_code = status_code


class NewsService:
    """NewsAPI üzerinden haber verisi sağlar."""

    def __init__(self, api_key: str) -> None:
        """Servisi API anahtarı ile başlatır.

        Args:
            api_key: NewsAPI erişim anahtarı.
        """
        if not api_key or not api_key.strip():
            raise ValueError("NewsAPI anahtarı boş olamaz.")
        self._api_key = api_key.strip()

    def get_turkey_headlines(
        self,
        category: str | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Türkiye güncel haber başlıklarını getirir.

        Args:
            category: Opsiyonel kategori (ör. technology, business).
            page_size: Döndürülecek haber sayısı (1-100).

        Returns:
            Sadeleştirilmiş haber sözlüklerinin listesi.

        Raises:
            ValueError: page_size geçersizse.
            NewsAPIError: API isteği başarısız olursa.
        """
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size 1 ile 100 arasında olmalıdır.")

        params: dict[str, str | int] = {
            "country": "tr",
            "pageSize": page_size,
            "apiKey": self._api_key,
        }
        if category:
            params["category"] = category.strip()

        try:
            response = requests.get(
                NEWS_API_BASE_URL,
                params=params,
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.Timeout as exc:
            raise NewsAPIError(
                "Haber servisi yanıt vermedi. Lütfen tekrar deneyin.",
                status_code=504,
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise NewsAPIError(
                "Haber servisine ulaşılamadı.",
                status_code=exc.response.status_code if exc.response else 502,
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise NewsAPIError(
                "Haber servisine bağlanırken bir hata oluştu.",
            ) from exc

        if payload.get("status") != "ok":
            message = payload.get("message", "Bilinmeyen NewsAPI hatası.")
            code = payload.get("code", "apiError")
            raise NewsAPIError(
                f"Haberler alınamadı ({code}): {message}",
                status_code=502,
            )

        return [self._normalize_article(item) for item in payload.get("articles", [])]

    def _normalize_article(self, raw: dict[str, Any]) -> dict[str, Any]:
        """API yanıtını uygulama formatına dönüştürür.

        Args:
            raw: NewsAPI'den gelen ham haber sözlüğü.

        Returns:
            Sadeleştirilmiş haber sözlüğü.
        """
        source = raw.get("source") or {}
        return {
            "title": raw.get("title"),
            "description": raw.get("description"),
            "url": raw.get("url"),
            "image_url": raw.get("urlToImage"),
            "published_at": raw.get("publishedAt"),
            "source_name": source.get("name") if isinstance(source, dict) else None,
        }
