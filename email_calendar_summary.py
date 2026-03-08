import anthropic
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

def get_google_services():
    """Authenticate and return Calendar + Gmail service clients."""
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    calendar = build("calendar", "v3", credentials=creds)
    gmail = build("gmail", "v1", credentials=creds)
    return calendar, gmail, creds.token

def fetch_events(calendar_service, days=7):
    """Fetch events for the next N days."""
    now = datetime.datetime.utcnow().isoformat() + "Z"
    end = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat() + "Z"
    result = calendar_service.events().list(
        calendarId="primary",
        timeMin=now,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    return result.get("items", [])

def format_events_for_claude(events):
    """Turn raw event list into a readable string for Claude."""
    if not events:
        return "No events found."
    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        lines.append(f"- {start}: {e.get('summary', 'No title')} | {e.get('description', '')}")
    return "\n".join(lines)

def generate_email_with_claude(events_text, your_email):
    """Use Claude to write a friendly calendar digest email."""
    client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var
    
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""You are a helpful assistant. Write a friendly, well-formatted 
calendar digest email for the following events. Group by day, use clear headings, 
and keep it concise. Address it to the owner of the calendar.

Events:
{events_text}

Format as a complete email body (no subject line needed)."""
        }]
    )
    return message.content[0].text

def send_email(gmail_service, to, subject, body):
    """Send an email via Gmail API."""
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail_service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    print(f"✅ Email sent to {to}")

def run_calendar_agent(your_email, days_ahead=7):
    print("🔐 Authenticating with Google...")
    calendar_svc, gmail_svc, _ = get_google_services()
    
    print(f"📅 Fetching events for the next {days_ahead} days...")
    events = fetch_events(calendar_svc, days=days_ahead)
    events_text = format_events_for_claude(events)
    
    print("🤖 Generating email digest with Claude...")
    email_body = generate_email_with_claude(events_text, your_email)
    
    today = datetime.date.today().strftime("%A, %d %B %Y")
    subject = f"📅 Your Calendar Digest — {today}"
    
    print("📨 Sending email...")
    send_email(gmail_svc, your_email, subject, email_body)

if __name__ == "__main__":
    run_calendar_agent(your_email="you@gmail.com", days_ahead=7)