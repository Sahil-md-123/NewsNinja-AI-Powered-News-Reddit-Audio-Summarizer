import asyncio
import os
from typing import Dict, List
import feedparser
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from utils import summarize_with_anthropic_news_script

load_dotenv()

class NewsScraper:
    _rate_limiter = AsyncLimiter(5, 1)

    def fetch_news_from_rss(self, topic: str) -> List[Dict]:
        topic_encoded = topic.replace(' ', '+')
        feed_url = f"https://news.google.com/rss/search?q={topic_encoded}&hl=en-US&gl=US&ceid=US:en"
        articles = []
        
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                articles.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', '')[:200]
                })
        except Exception as e:
            print(f"RSS Error: {e}")
        
        return articles

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def scrape_news(self, topics: List[str]) -> Dict[str, Dict]:
        results = {}
        
        for topic in topics:
            async with self._rate_limiter:
                try:
                    print(f"Fetching news for: {topic}")
                    articles = self.fetch_news_from_rss(topic)
                    
                    if not articles:
                        results[topic] = "No recent news found."
                        continue
                    
                    headlines_text = "\n\n".join([
                        f"{article['title']}\n{article['summary']}"
                        for article in articles
                    ])
                    
                    summary = summarize_with_anthropic_news_script(
                        api_key=os.getenv("ANTHROPIC_API_KEY"),
                        headlines=headlines_text
                    )
                    
                    results[topic] = summary
                    print(f"✅ Success: {topic}")
                    
                except Exception as e:
                    results[topic] = f"Error: {str(e)}"
                
                await asyncio.sleep(1)
        
        return {"news_analysis": results}