"""
Daily AI Analyst Briefing Agent
================================
Searches for the latest AI news across 4 focus areas, generates a structured
email digest and a ready-to-post LinkedIn draft, then sends it via Gmail.

Setup:
  1. pip install anthropic google-auth-oauthlib google-api-python-client python-dotenv
  2. Add credentials.json (Google OAuth) to this folder
  3. Create a .env file (see .env.example)
  4. Run once manually to authenticate: python ai_briefing_agent.py
  5. Schedule via cron: 0 8 * * * python /path/to/ai_briefing_agent.py

Cron reminder:
  - Run `crontab -e` and add the line above (adjust path and time as needed)
"""

import os
import json
import pickle
import base64
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import anthropic
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
YOUR_EMAIL        = os.getenv("GMAIL_ADDRESS")
YOUR_NAME         = os.getenv("YOUR_NAME", "there")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]

FOCUS_AREAS = [
    "new AI models and capabilities breakthroughs",
    "AI startup funding rounds and acquisitions",
    "AI impact on job market and analyst/data roles",
    "data analytics tooling AI updates (dbt, BigQuery, Tableau, BI tools)",
]

ANALYST_PERSONA = """
You are an expert AI analyst with deep knowledge of the data and analytics industry.
You are briefing a Lead Data Analyst at a digital media company who works with BigQuery,
dbt, Tableau, and GA4 daily. They care about:
- What AI developments could affect their role or team
- Tools that could make analysts more productive
- Signals about where the industry is heading
- Startup activity that might produce new tooling or competitors
Filter everything through this lens. Be direct, insightful, and skip generic hype.
"""

# ── Google Auth ───────────────────────────────────────────────────────────────

def get_gmail_service():
    """Authenticate and return Gmail service. Opens browser on first run only."""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)

# ── Tools (what the agent can do) ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "search_ai_news",
        "description": (
            "Search the web for the latest news on a specific AI topic. "
            "Returns headlines and summaries from the past 24 hours."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The specific topic to search for, e.g. 'AI startup funding 2025'"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "send_briefing_email",
        "description": "Send the final briefing email to the user via Gmail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject":        {"type": "string", "description": "Email subject line"},
                "html_body":      {"type": "string", "description": "Full HTML email body with digest"},
                "linkedin_draft": {"type": "string", "description": "Plain text LinkedIn post draft"}
            },
            "required": ["subject", "html_body", "linkedin_draft"]
        }
    }
]

# ── Tool implementations ───────────────────────────────────────────────────────

def search_ai_news(topic: str) -> str:
    """
    Uses a secondary Claude call to simulate a web search summary.
    In production, swap this for a real search API (Brave, Serper, Tavily).
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.date.today().strftime("%B %d, %Y")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": (
                f"Today is {today}. Summarise the most important recent developments "
                f"(last 24-48 hours) on this topic: '{topic}'. "
                f"Return 2-3 specific stories with a headline and 2-sentence summary each. "
                f"Be factual and specific — no filler."
            )
        }]
    )
    return response.content[0].text


def send_briefing_email(gmail_service, subject: str, html_body: str, linkedin_draft: str) -> str:
    """Send the digest email with LinkedIn draft appended."""
    full_html = f"""
    <html><body>
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: auto; color: #222;">
        {html_body}
        <hr style="margin: 40px 0; border: none; border-top: 1px solid #ddd;">
        <h2 style="color: #0077b5;">📝 LinkedIn Draft</h2>
        <div style="background: #f0f7ff; border-left: 4px solid #0077b5; padding: 16px; border-radius: 4px;">
            <pre style="white-space: pre-wrap; font-family: Arial, sans-serif; font-size: 14px;">{linkedin_draft}</pre>
        </div>
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            Generated by your Daily AI Briefing Agent · {datetime.date.today().strftime("%A, %d %B %Y")}
        </p>
    </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["to"]      = YOUR_EMAIL
    msg["subject"] = subject
    msg.attach(MIMEText(full_html, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail_service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"Email sent to {YOUR_EMAIL}"

# ── Agent loop ────────────────────────────────────────────────────────────────

def run_agent():
    client       = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    gmail_service = get_gmail_service()
    today        = datetime.date.today().strftime("%A, %d %B %Y")

    print(f"🤖 Agent starting — {today}")

    # Initial prompt — Claude decides what to search and how to structure the output
    messages = [{
        "role": "user",
        "content": (
            f"Today is {today}. You are producing a daily AI briefing for a Lead Data Analyst.\n\n"
            f"Step 1: Search for recent news across these 4 focus areas:\n"
            + "\n".join(f"  - {area}" for area in FOCUS_AREAS) +
            f"\n\nStep 2: Synthesise what you find into a structured HTML email digest with:\n"
            f"  - A brief top-line summary (2-3 sentences, the most important thing today)\n"
            f"  - One section per focus area with the key story and why it matters for data analysts\n"
            f"  - A 'Signal vs Noise' verdict at the end: what's genuinely important vs overhyped\n\n"
            f"Step 3: Pick the single most interesting story and write a LinkedIn post (150-200 words):\n"
            f"  - Written in first person as a data analyst sharing a genuine observation\n"
            f"  - Conversational, not corporate\n"
            f"  - End with a question to prompt engagement\n"
            f"  - Include 3-4 relevant hashtags\n\n"
            f"Then send the email using the send_briefing_email tool.\n\n"
            f"Analyst persona to keep in mind:\n{ANALYST_PERSONA}"
        )
    }]

    # Agentic loop — Claude runs until it decides it's done
    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages
        )

        print(f"   stop_reason: {response.stop_reason}")

        if response.stop_reason == "end_turn":
            print("✅ Agent completed.")
            break

        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"   🔧 Calling tool: {block.name} | input: {json.dumps(block.input)[:80]}...")

                    if block.name == "search_ai_news":
                        result = search_ai_news(block.input["topic"])

                    elif block.name == "send_briefing_email":
                        result = send_briefing_email(
                            gmail_service,
                            subject        = block.input["subject"],
                            html_body      = block.input["html_body"],
                            linkedin_draft = block.input["linkedin_draft"]
                        )
                        print(f"   📨 {result}")

                    else:
                        result = f"Unknown tool: {block.name}"

                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result
                    })

            # Feed results back so Claude can continue
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user",      "content": tool_results})

        else:
            print(f"⚠️  Unexpected stop_reason: {response.stop_reason}")
            break

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_agent()