# Reddit AITAH Bot

**⚠️ EDUCATIONAL PURPOSE ONLY ⚠️**

AI-powered Reddit bot for r/AITAH subreddit using OpenRouter API.

## 🚀 DigitalOcean Deployment ($4/month)

### Step 1: Create DigitalOcean Droplet
1. Go to [DigitalOcean](https://cloud.digitalocean.com/)
2. Create Droplet → **Docker on Ubuntu 22.04**
3. Choose **Basic $4/month** (1GB RAM, 1 vCPU)
4. Add your SSH key
5. Create droplet

### Step 2: Deploy Bot
```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Clone repository
git clone https://github.com/your-username/reddit_karma_farmer_auto_commentator_with_AI.git
cd reddit_karma_farmer_auto_commentator_with_AI

# Setup environment
cp .env.example .env
nano .env  # Add your credentials (see below)

# Start bot
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🔧 Environment Setup

Edit `.env` with your credentials:

```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret  
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
OPENROUTER_API_KEY=your_openrouter_api_key
SITE_URL=https://localhost
SITE_NAME=Reddit Bot
```

### Get API Keys:
- **Reddit**: https://www.reddit.com/prefs/apps (create "script" app)
- **OpenRouter**: https://openrouter.ai (sign up for API key)

## 📊 Bot Settings

- **Target**: r/AITAH only
- **Frequency**: 10-20 minutes between comments  
- **Daily Limit**: 50 comments max
- **Post Age**: Under 2 hours old

## 🛠️ Management Commands

```bash
# Start bot
docker-compose up -d

# Stop bot  
docker-compose down

# View logs
docker-compose logs -f

# Update bot
git pull && docker-compose up -d --pull
```

## 💰 Total Cost: $4/month

Perfect for running 24/7 with room to spare.

## 📋 Disclaimer

Educational proof of concept. Use responsibly and follow Reddit's Terms of Service.