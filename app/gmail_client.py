import base64
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Read-only: this key can never send, delete, or change mail.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def list_newest_subjects(n=5):
    service = get_service()
    result = service.users().messages().list(userId="me", maxResults=n).execute()
    subjects = []
    for msg in result.get("messages", []):
        full = service.users().messages().get(
            userId="me", id=msg["id"], format="metadata", metadataHeaders=["Subject"]
        ).execute()
        headers = full["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")
        subjects.append(subject)
    return subjects

def _get_body(payload):
    """Find the plain-text part of an email and decode it."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    for part in payload.get("parts", []):
        text = _get_body(part)
        if text:
            return text
    return ""


def fetch_emails(n=5):
    """Pull the n newest emails and shape each one like EmailState."""
    service = get_service()
    result = service.users().messages().list(userId="me", maxResults=n).execute()
    emails = []
    for msg in result.get("messages", []):
        full = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
        emails.append({
            "email_id": msg["id"],
            "sender": headers.get("From", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "body": _get_body(full["payload"]),
            "category": None,
            "label": None,
            "draft": None,
            "approved": False,
        })
    return emails


if __name__ == "__main__":
    for s in list_newest_subjects():
        print(s)