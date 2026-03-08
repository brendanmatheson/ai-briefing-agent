# 🤖 Daily AI Analyst Briefing Agent

> ⚠️ Never commit your `.env`, `credentials.json`, or `token.pickle`.
> See `.env.example` for the required environment variables.

---

## About this project

This is a learning project and my first attempt at building an AI agent from scratch.

I'm a data analyst by trade and I wanted to get hands-on with LLM tooling beyond just using ChatGPT or Claude in the browser. The goal was to understand how agents actually work — how Claude decides which tools to call, how to wire up real APIs, how to schedule and automate the whole thing — by building something I'd genuinely use every day.

The result is a personal briefing agent that monitors AI developments relevant to data and analytics roles, emails me a digest each morning, and drafts a LinkedIn post for the most interesting story of the day.

If you're an analyst or data professional curious about building with LLMs, I hope this is a useful starting point. It's not production code — it's a learning exercise, built in public.

---

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

## What makes it an agent (not just a script)

Rather than following a fixed sequence of steps, Claude drives the process — it decides which tools to call, in what order, and when it's done. You give it a goal and a set of tools; it figures out the rest. This is the core idea behind agentic LLM applications and what I wanted to understand by building this.

---

## Setup

### 1. Install dependencies
```bash
pip install anthropic google-auth-oauthlib google-api-python-client python-dotenv tavily-python
```

### 2. Get your credentials

**Anthropic API key:** https://console.anthropic.com

**Tavily API key (live news search):** https://tavily.com — free tier is plenty for personal use

**Google OAuth credentials:**
- Go to https://console.cloud.google.com
- Create a project
- Enable the Gmail API (APIs & Services → Library → search Gmail API → Enable)
- Go to APIs & Services → Credentials → Create OAuth 2.0 Client ID (Desktop app)
- Download the JSON and save it as `credentials.json` in this folder
- Go to OAuth consent screen → Test users → add your Gmail address

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your real values
```

### 4. First run (authenticates with Google)
```bash
python ai_briefing_agent.py
```
A browser window will open asking you to sign in to Google. This only happens once — the token is saved locally for all future runs.

### 5. Schedule it (runs automatically every morning)
```bash
crontab -e
# Add this line (runs at 8am daily):
0 8 * * * /usr/bin/python3 /full/path/to/ai_briefing_agent.py
```

---

## Security

- Never commit `.env`, `credentials.json`, or `token.pickle` — all are covered by `.gitignore`
- The OAuth app runs in "test" mode, so only accounts you explicitly whitelist can authenticate
- Lock down local file permissions: `chmod 600 credentials.json token.pickle`

---

## Stack

- [Anthropic API](https://console.anthropic.com) — Claude as the agent brain
- [Tavily](https://tavily.com) — live web search built for AI agents
- [Gmail API](https://developers.google.com/gmail/api) — sending the daily digest
- Python, python-dotenv, google-auth-oauthlib

---

## What's next

- Add a memory layer so the agent tracks themes across days and spots trends over time
- Slack notification as an alternative to email
- A simple web UI to review and edit the LinkedIn draft before posting
