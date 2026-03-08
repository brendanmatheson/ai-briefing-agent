# 🤖 Daily AI Analyst Briefing Agent

A personal AI agent that searches for the latest developments in AI every morning and emails you a structured digest + a ready-to-post LinkedIn draft.

Built with the Anthropic API (Claude) and Gmail API.

## What it does

Every morning the agent:
1. Searches for recent news across 4 focus areas:
   - New AI models & capabilities
   - Startup funding & acquisitions
   - AI impact on jobs & analyst roles
   - Data tooling updates (dbt, BigQuery, Tableau etc.)
2. Synthesises findings into a structured email digest
3. Writes a LinkedIn post based on the day's most interesting story
4. Sends everything to your inbox

## Setup

### 1. Install dependencies
```bash
pip install anthropic google-auth-oauthlib google-api-python-client python-dotenv
```

### 2. Get your credentials

**Anthropic API key:** https://console.anthropic.com

**Google OAuth credentials:**
- Go to https://console.cloud.google.com
- Create a project
- Enable the Gmail API
- Go to APIs & Services → Credentials → Create OAuth 2.0 Client ID (Desktop app)
- Download the JSON and save it as `credentials.json` in this folder

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your real values
```

### 4. First run (authenticates with Google)
```bash
python ai_briefing_agent.py
```
A browser window will open asking you to sign in to Google. This only happens once — the token is saved locally.

### 5. Schedule it (runs automatically every morning)
```bash
crontab -e
# Add this line (runs at 8am daily):
0 8 * * * /usr/bin/python3 /full/path/to/ai_briefing_agent.py
```

## Security

- Never commit `.env`, `credentials.json`, or `token.pickle` — all are in `.gitignore`
- The OAuth app runs in "test" mode, so only your Google account can authenticate with it
- File permissions: `chmod 600 credentials.json token.pickle`

## Upgrading to real web search (V2)

The `search_ai_news` function currently uses Claude's training knowledge. For live results, replace it with a real search API:
- [Brave Search API](https://brave.com/search/api/) — generous free tier
- [Tavily](https://tavily.com) — built for AI agents
- [Serper](https://serper.dev) — Google results via API
