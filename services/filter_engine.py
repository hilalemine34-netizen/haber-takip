from collections import defaultdict
from models.article import NewsArticle
from models.interaction import Interaction
from models.preference import UserPreference




class FilterEngine:

    def __init__(self, interaction_repo, news_repo):
        self.interaction_repo = interaction_repo
        self.news_repo = news_repo


    #  PROFİL (Kullanıcı Davranış Analizi)
   
    def build_user_profile(self, user_id):
        behavior_scores = defaultdict(int)
        preference_scores = defaultdict(int)

        interactions = self.interaction_repo.get_user_interactions(user_id) or []

        for inter in interactions:

            article = self.news_repo.get_article_by_id(inter.article_id)
            if not article:
                continue

            categories_str = article.categories or ""
            categories = [c.strip() for c in categories_str.split(",")] if categories_str else []

            for cat in categories:
                behavior_scores[cat] += inter.score()

        preferences = self.interaction_repo.get_user_preferences(user_id) or []

        for pref in preferences:
            if not pref.is_valid():
                continue

            category_name = self.news_repo.get_category_name(pref.category_id)

            if category_name and pref.matches_category(pref.category_id):
                preference_scores[category_name] += 1

        return behavior_scores, preference_scores

    

    #  RECOMMEND 
 
    def recommend(self, user_id, limit=10):

        liked_articles = self.interaction_repo.get_user_liked_articles(user_id) or []
        favorite_articles = self.interaction_repo.get_user_favorites(user_id) or []
        all_articles = self.news_repo.get_all_articles()

        behavior_scores, preference_scores = self.build_user_profile(user_id)

       
        if not behavior_scores and not preference_scores:
            return self.news_repo.get_trending_articles(limit)

       
        combined_scores = {}
        all_cats = set(behavior_scores) | set(preference_scores)

        for cat in all_cats:
            combined_scores[cat] = (
                behavior_scores.get(cat, 0) * 0.3 +
                preference_scores.get(cat, 0) * 0.7
            )

        scored_list = []
        

        for article in all_articles:

            # kategoriler
            art_cats_str = article.categories or ""
            art_cats = (
                [c.strip() for c in art_cats_str.split(",")]
                if art_cats_str else []
            )

            # kategori skoru
            cat_score = sum(combined_scores.get(cat, 0) for cat in art_cats)

            # popülerlik skoru
            popularity_score = (
                (article.view_count or 0) * 0.2 +
                (article.like_count or 0) * 0.5
            )

          
            article.internal_score = cat_score + popularity_score

            scored_list.append(article)

       
        ai_articles = sorted(
            [a for a in scored_list if getattr(a, "internal_score", 0) > 0],
            key=lambda x: x.internal_score,
            reverse=True
        )


        final_pool = [
    self._to_object(a)
    for a in (liked_articles + favorite_articles + ai_articles)
]

        seen_ids = set()
        unique_results = []

        for art in final_pool:
            if art.id not in seen_ids:
                unique_results.append(art)
                seen_ids.add(art.id)

        return unique_results[:limit]

   
    #  COLD START
  
    def cold_start(self, limit=10):
        articles = self.news_repo.get_trending_articles(limit * 2)

        return sorted(
            articles,
            key=lambda x: x.published_date or "",
            reverse=True
        )[:limit]
    
    def _to_object(self, data):
        if isinstance(data, NewsArticle):
            return data

        return NewsArticle(
            article_id=data.get("id"),
            title=data.get("title"),
            content=data.get("content"),
            article_url=data.get("article_url"),
            source_id=data.get("source_id"),
            published_date=data.get("published_date"),
            created_at=data.get("created_at"),
            view_count=data.get("view_count", 0),
            like_count=data.get("like_count", 0),
            source_name=data.get("source_name"),
            categories=data.get("categories"),
            image_url=data.get("image_url"),
            
            
        )

   

    

    