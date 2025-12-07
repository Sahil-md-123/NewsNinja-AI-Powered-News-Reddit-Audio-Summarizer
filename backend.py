from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

from models import NewsRequest
from utils import generate_broadcast_news, tts_to_audio
from news_scraper import NewsScraper

# Only import reddit_scraper if not in Streamlit environment
try:
    from reddit_scraper import scrape_reddit_topics
    REDDIT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Reddit scraper not available: {e}")
    REDDIT_AVAILABLE = False
    
    # Define dummy function
    async def scrape_reddit_topics(topics):
        return {"reddit_analysis": {t: "Reddit scraping not available in this environment" for t in topics}}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NewsNinja API")
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "healthy", 
        "service": "NewsNinja API",
        "reddit_available": REDDIT_AVAILABLE
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "reddit_scraping": REDDIT_AVAILABLE
    }

@app.post("/generate-news-audio")
async def generate_news_audio(request: NewsRequest):
    try:
        logger.info(f"Request: {request.topics}, source: {request.source_type}")
        results = {}
        
        if request.source_type in ["news", "both"]:
            try:
                news_scraper = NewsScraper()
                results["news"] = await news_scraper.scrape_news(request.topics)
            except Exception as e:
                logger.error(f"News error: {e}")
                results["news"] = {"news_analysis": {t: f"Error: {e}" for t in request.topics}}
        
        if request.source_type in ["reddit", "both"]:
            if not REDDIT_AVAILABLE:
                logger.warning("Reddit scraping requested but not available")
                results["reddit"] = {"reddit_analysis": {t: "Reddit scraping not available" for t in request.topics}}
            else:
                try:
                    results["reddit"] = await scrape_reddit_topics(request.topics)
                except Exception as e:
                    logger.error(f"Reddit error: {e}")
                    results["reddit"] = {"reddit_analysis": {t: f"Error: {e}" for t in request.topics}}

        news_summary = generate_broadcast_news(
            api_key=os.getenv("GROQ_API_KEY"),
            news_data=results.get("news", {}),
            reddit_data=results.get("reddit", {}),
            topics=request.topics
        )
        
        audio_path = tts_to_audio(text=news_summary, language='en')

        if not audio_path or not Path(audio_path).exists():
            raise HTTPException(status_code=500, detail="Audio generation failed")
        
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        
        try:
            os.remove(audio_path)
        except:
            pass
        
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=news-summary.mp3"}
        )
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    Path("audio").mkdir(exist_ok=True)
    uvicorn.run("backend:app", host="0.0.0.0", port=1234, reload=True)
   
               
           
       
