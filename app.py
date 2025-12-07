import streamlit as st
import feedparser
from gtts import gTTS
import tempfile
import os

st.set_page_config(page_title="NewsNinja", page_icon="🎙️", layout="wide")

def fetch_news_rss(topic: str, max_articles: int = 10):
    """Fetch news from Google News RSS"""
    topic_encoded = topic.replace(' ', '+')
    feed_url = f"https://news.google.com/rss/search?q={topic_encoded}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        for entry in feed.entries[:max_articles]:
            articles.append({
                'title': entry.get('title', ''),
                'summary': entry.get('summary', '')[:200],
                'link': entry.get('link', '')
            })
        return articles
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

def summarize_with_groq(headlines: str, api_key: str):
    """Summarize headlines using Groq API"""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional news broadcaster. Create a natural, conversational news broadcast script suitable for text-to-speech. Start directly with the news without any preamble. Use clear, simple language in paragraph form. Aim for 60-120 seconds of content when read aloud."
                },
                {
                    "role": "user", 
                    "content": f"Create a broadcast news script from these headlines:\n\n{headlines}"
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except ImportError:
        return "Error: Groq library not installed. Please check requirements."
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def generate_audio(text: str):
    """Generate audio using Google Text-to-Speech"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"Audio generation error: {e}")
        return None

def main():
    # Header
    st.title("🎙️ NewsNinja")
    st.markdown("### AI-Powered News Audio Summarizer")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Groq API Key", 
            type="password",
            help="Get your free API key from console.groq.com"
        )
        
        if not api_key:
            st.warning("⚠️ Enter your Groq API key to continue")
            st.info("📌 Get a free key at [console.groq.com](https://console.groq.com)")
        
        st.divider()
        
        # Settings
        max_articles = st.slider("Max articles to fetch", 5, 20, 10)
        
        st.divider()
        
        # Info
        st.markdown("### ℹ️ About")
        st.caption("NewsNinja fetches latest news and converts it to audio summaries using AI.")
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        topic = st.text_input(
            "🔍 Enter a topic",
            placeholder="e.g., Artificial Intelligence, Climate Change, Sports",
            help="Enter any topic to get the latest news"
        )
    
    with col2:
        st.write("")
        st.write("")
        generate_btn = st.button(
            "🚀 Generate",
            type="primary",
            use_container_width=True,
            disabled=not api_key or not topic
        )
    
    # Generate audio summary
    if generate_btn:
        if not api_key:
            st.error("❌ Please enter your Groq API key in the sidebar")
        elif not topic:
            st.error("❌ Please enter a topic")
        else:
            with st.spinner("🔄 Processing..."):
                # Step 1: Fetch news
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📰 Fetching latest news...")
                progress_bar.progress(25)
                articles = fetch_news_rss(topic, max_articles)
                
                if not articles:
                    st.error(f"❌ No news found for topic: {topic}")
                    return
                
                # Show fetched articles
                status_text.text(f"✅ Found {len(articles)} articles")
                progress_bar.progress(50)
                
                with st.expander(f"📄 View {len(articles)} articles"):
                    for i, article in enumerate(articles, 1):
                        st.markdown(f"**{i}. {article['title']}**")
                        st.caption(article['summary'])
                        if article.get('link'):
                            st.markdown(f"[Read more →]({article['link']})")
                        st.divider()
                
                # Step 2: Generate summary
                status_text.text("🤖 Generating AI summary...")
                progress_bar.progress(75)
                
                headlines_text = "\n\n".join([
                    f"Headline: {article['title']}\nSummary: {article['summary']}"
                    for article in articles
                ])
                
                summary = summarize_with_groq(headlines_text, api_key)
                
                # Show script
                with st.expander("📝 View broadcast script"):
                    st.markdown(summary)
                
                # Step 3: Generate audio
                status_text.text("🎵 Converting to audio...")
                progress_bar.progress(90)
                
                audio_path = generate_audio(summary)
                
                if audio_path and os.path.exists(audio_path):
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    
                    st.success("🎉 Audio summary generated successfully!")
                    
                    # Play audio
                    with open(audio_path, 'rb') as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mpeg")
                        
                        # Download button
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            st.download_button(
                                "⬇️ Download Audio",
                                data=audio_bytes,
                                file_name=f"newsninja-{topic.replace(' ', '-')[:30]}.mp3",
                                mime="audio/mpeg",
                                use_container_width=True
                            )
                    
                    # Cleanup
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                else:
                    st.error("❌ Failed to generate audio")
    
    # Instructions at the bottom
    st.divider()
    
    with st.expander("📖 How to use NewsNinja"):
        st.markdown("""
### Quick Start Guide

1. **Get API Key (Free)**
   - Visit [console.groq.com](https://console.groq.com)
   - Sign up for a free account
   - Copy your API key

2. **Enter API Key**
   - Paste it in the sidebar (left side)

3. **Enter Topic**
   - Type any topic (e.g., "Technology", "Sports", "AI")

4. **Generate**
   - Click the "🚀 Generate" button
   - Wait 10-30 seconds

5. **Listen or Download**
   - Play the audio directly
   - Download the MP3 file

### Features
- ✅ Latest news from Google News RSS
- ✅ AI-powered summarization
- ✅ Natural text-to-speech conversion
- ✅ Download audio files
- ✅ No backend required

### Tips
- Be specific with topics for better results
- Try topics like "AI", "Climate Change", "Space Exploration"
- Adjust max articles in sidebar for more/less content
        """)
    
    # Footer
    st.divider()
    st.caption("🎙️ NewsNinja - AI-Powered News Summarizer | Powered by Groq AI & Google TTS")

if __name__ == "__main__":
    main()
