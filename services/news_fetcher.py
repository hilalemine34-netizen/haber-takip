import requests
from newspaper import Article
from repositories.news_repository import NewsRepository
import time
import logging
from models.article import NewsArticle
from datetime import datetime
from models.tracking_log import TrackingLog

logging.basicConfig(level=logging.INFO)


class NewsFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.repo = NewsRepository()
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    def fetch(self, category="general"):
        url = f"{self.base_url}/top-headlines?country=us&category={category}&apiKey={self.api_key}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()

            log = TrackingLog(
                log_id=None,
                source_id=1,
                status="SUCCESS",
                message=f"{category} verisi başarıyla çekildi"
            )

            logging.info(log.summary())

            return data.get("articles", [])

        except requests.exceptions.Timeout:

            log = TrackingLog(
                log_id=None,
                source_id=1,
                status="TIMEOUT",
                message=f"{category} API timeout oldu"
            )

            if log.is_timeout():
                logging.warning(log.summary())

            return []

        except Exception as e:

            log = TrackingLog(
                log_id=None,
                source_id=1,
                status="FAILED",
                message=str(e)
            )

            if log.is_failed():
                logging.error(log.summary())

            return []

    
    def get_full_content(self, url, fallback):
    

        try:
            article = Article(url)
            article.config.browser_user_agent = self.headers["User-Agent"]
            article.config.request_timeout = 10

    
            for i in range(3):
                try:
                    article.download()
                    article.parse()
                    break
                except Exception as e:
                    log = TrackingLog(
                        log_id=None,
                        source_id=1,
                        status="TIMEOUT",
                        message=f"Deneme {i+1}: içerik çekilemedi - {str(e)}"
                    )

                    if log.is_timeout():
                        logging.warning(log.summary())

                    time.sleep(2)
            else:
       
                log = TrackingLog(
                    log_id=None,
                    source_id=1,
                    status="FAILED",
                    message="3 deneme sonrası içerik alınamadı"
                )

                if log.is_failed():
                    logging.error(log.summary())

                return fallback or "İçerik bulunamadı."

    
            content = article.text

            if not content or len(content.strip()) < 200:
                log = TrackingLog(
                    log_id=None,
                    source_id=1,
                    status="FAILED",
                    message="İçerik çok kısa veya boş"
                )

                logging.warning(log.summary())

                return fallback or "İçerik bulunamadı."

 
            log = TrackingLog(
                log_id=None,
                source_id=1,
                status="SUCCESS",
                message="İçerik başarıyla çekildi"
            )

            if log.is_success():
                logging.info(log.summary())

            return content[:3000]

        except Exception as e:
 
            log = TrackingLog(
                log_id=None,
                source_id=1,
                status="FAILED",
                message=f"Genel hata: {str(e)}"
            )

            if log.is_failed():
                logging.error(log.summary())

            return fallback or "İçerik bulunamadı."
        
    def resolve_url(self, url):
        try:
            response = requests.get(url, allow_redirects=True, timeout=5)
            return response.url
        except:
            return url
        
    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception as e:
                logging.warning(f"Tarih parse edilemedi: {date_str} - {e}")
                return None


    def _map_api_to_model(self, data: dict) -> NewsArticle:
        return NewsArticle(
            article_id=None,
            title=data.get("title"),
            content=data.get("content") or data.get("description"),
            article_url=data.get("url"),
            source_id=None,

         
            published_date=self._parse_date(data.get("publishedAt")),

            created_at=None,
            view_count=0,
            like_count=0,

            source_name=(data.get("source") or {}).get("name")
            if isinstance(data.get("source"), dict)
            else data.get("source_name"),

            categories=data.get("category"),

     
            image_url=data.get("urlToImage") or data.get("image_url")
        )


    def run(self):
        categories = [
            "technology",
            "business",
            "sports",
            "science",
            "entertainment",
            "health",
        ]

        all_articles = self.repo.get_all_articles()

        #  object üzerinden duplicate set
        existing_titles = {
            (a.title or "").lower().strip()
            for a in all_articles
            if a.title
        }

        for cat in categories:
            logging.info(f"🔄 {cat.upper()} kategorisi çekiliyor...")

            raw_articles = self.fetch(cat)

            fetched_articles = [
                self._map_api_to_model(a)
                for a in raw_articles
                if a.get("title")
            ]

            for article in fetched_articles:
                if article.source_name == "Google News":
                    continue
                time.sleep(0.5)

                if not article.title or not article.article_url:
                    continue

                clean_title = article.title.lower().strip()

                # duplicate kontrol
                if clean_title in existing_titles:
                    logging.info(f"⏩ Atlandı (Zaten var): {article.title[:40]}")
                    continue

                #  içerik çek
                real_url = self.resolve_url(article.article_url)
                article.content = self.get_full_content(
                real_url,
                article.content
            )


                try:
                    self.repo.save_article(
                        title=article.title,
                        content=article.content,
                        url=real_url,   
                        image_url=article.image_url,
                        category=cat,
                        source_name=article.source_name or "Unknown",
                    )

                    existing_titles.add(clean_title)

                    log = TrackingLog(
                        log_id=None,
                        source_id=1,
                        status="SUCCESS",
                        message=f"DB kayıt başarılı: {article.title[:50]}"
                    )

                    logging.info(log.summary())

                except Exception as e:
                    log = TrackingLog(
                    log_id=None,
                    source_id=1,
                    status="FAILED",
                    message=str(e)
                )

                    logging.error(log.summary())

        logging.info("Tüm kategoriler güncellendi.")