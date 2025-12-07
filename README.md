# 🎙️ NewsNinja - AI News Audio Summarizer

Generates audio summaries from news articles and Reddit discussions.

## Features
- 📰 Google News RSS scraping
- 🗣️ Reddit discussion analysis via MCP
- 🎵 Text-to-speech audio generation
- 🤖 AI-powered summarization (Anthropic, Groq)

## Setup

### Prerequisites
- Python 3.9+
- API Keys: Anthropic, Groq, BrightData

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/newsninja-audio-summarizer.git
cd newsninja-audio-summarizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```env
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
BRIGHTDATA_API_KEY=your_key_here
BRIGHTDATA_WEB_UNLOCKER_ZONE=your_zone
API_TOKEN=your_token
WEB_UNLOCKER_ZONE=your_zone
```

### Running Locally

**Backend:**
```bash
python backend.py
```

**Frontend (in new terminal):**
```bash
streamlit run frontend.py
```

Visit: `http://localhost:8501`

## Deployment

### Backend (Render/Railway)
1. Connect GitHub repo
2. Add environment variables
3. Deploy

### Frontend (Streamlit Cloud)
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect repository
3. Set main file: `frontend.py`
4. Add secret: `BACKEND_URL = "your-backend-url"`

## Tech Stack
- **Frontend**: Streamlit
- **Backend**: FastAPI
- **AI Models**: Claude (Anthropic), Llama (Groq)
- **TTS**: Google Text-to-Speech
- **Scraping**: BrightData MCP, RSS feeds

## License
MIT