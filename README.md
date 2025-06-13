# AITAH Comment Bot

**⚠️ EXPERIMENTAL PROOF OF CONCEPT ⚠️**

This is an experimental proof of concept for educational purposes only. This project demonstrates AI-powered Reddit commenting on AITAH (Am I The Asshole) subreddits using OpenRouter API.

## Setup

1. **Install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Get API credentials**
   - Reddit: https://www.reddit.com/prefs/apps (create script app)
   - OpenRouter: https://openrouter.ai (get API key)

4. **Test and run**
   ```bash
   python test_config.py
   python main.py
   ```

## Environment Variables

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
OPENROUTER_API_KEY=your_openrouter_key
SITE_URL=https://localhost:8080
SITE_NAME=AITAH Comment Bot
```

## Files

- `main.py` - Bot logic
- `generator_comment.py` - AI comment generation
- `config.py` - Environment loader
- `test_config.py` - Configuration tester
- `.env` - Your credentials (not in git)

## Disclaimer

This is a proof of concept for educational purposes. Use responsibly and in compliance with Reddit's Terms of Service.