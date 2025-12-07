from urllib.parse import quote_plus
from dotenv import load_dotenv
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from gtts import gTTS
import groq

load_dotenv()

AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

def generate_valid_news_url(keyword: str) -> str:
    q = quote_plus(keyword)
    return f"https://news.google.com/search?q={q}&tbs=sbd:1"

def generate_news_urls_to_scrape(list_of_keywords):
    return {kw: generate_valid_news_url(kw) for kw in list_of_keywords}

def scrape_with_brightdata(url: str) -> str:
    headers = {"Authorization": f"Bearer {os.getenv('BRIGHTDATA_API_KEY')}", "Content-Type": "application/json"}
    payload = {"zone": os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE'), "url": url, "format": "raw"}
    try:
        response = requests.post("https://api.brightdata.com/request", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise Exception(f"BrightData error: {str(e)}")

def clean_html_to_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n").strip()

def extract_headlines(cleaned_text: str) -> str:
    headlines = []
    current_block = []
    lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
    for line in lines:
        if line == "More":
            if current_block:
                headlines.append(current_block[0])
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        headlines.append(current_block[0])
    return "\n".join(headlines)

def generate_broadcast_news(api_key, news_data, reddit_data, topics):
    system_prompt = "You are a news reporter. Create TTS-ready news. Start directly, 60-120 sec per topic, natural speech, paragraphs only."
    topic_blocks = []
    for topic in topics:
        nc = news_data.get("news_analysis", {}).get(topic, '') if news_data else ''
        rc = reddit_data.get("reddit_analysis", {}).get(topic, '') if reddit_data else ''
        ctx = []
        if nc and not nc.startswith('Error'):
            ctx.append(f"NEWS: {nc}")
        if rc and not rc.startswith('Error'):
            ctx.append(f"REDDIT: {rc}")
        if ctx:
            topic_blocks.append(f"TOPIC: {topic}\n" + "\n".join(ctx))
    if not topic_blocks:
        return "No information available."
    
    user_prompt = "Create broadcast:\n\n" + "\n\n".join(topic_blocks)
    
    client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    return response.choices[0].message.content

def summarize_with_anthropic_news_script(api_key: str, headlines: str) -> str:
    system_prompt = "News editor: Headlines to TTS script. No special chars, no preamble, speech-ready."
    
    client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": headlines}
        ],
        temperature=0.4,
        max_tokens=1000
    )
    return response.choices[0].message.content

def tts_to_audio(text: str, language: str = 'en') -> str:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = AUDIO_DIR / f"tts_{timestamp}.mp3"
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(str(filename))
        return str(filename)
    except Exception as e:
        print(f"gTTS Error: {e}")
        return None