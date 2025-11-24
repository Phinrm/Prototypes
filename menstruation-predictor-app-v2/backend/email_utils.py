# backend/email_utils.py
import base64
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build


# You must create a Google Cloud project + service account with Gmail API enabled,
# then download the JSON key file and set its path here or via env var.
SERVICE_ACCOUNT_FILE = "service-account.json"  # (place in backend/)
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
GMAIL_SENDER = "your-sender-email@gmail.com"  # must be allowed / delegated


def get_gmail_service():
  creds = service_account.Credentials.from_service_account_file(
      SERVICE_ACCOUNT_FILE,
      scopes=GMAIL_SCOPES,
  )
  # For domain-wide delegation, you may need: creds = creds.with_subject(GMAIL_SENDER)
  service = build("gmail", "v1", credentials=creds)
  return service


def send_password_reset_email(to_email: str, reset_link: str):
  service = get_gmail_service()

  body = f"""
Hi there,

You (or someone using this email) requested a password reset for PinkCycle.

Click this link to reset your password:

  {reset_link}

If you didn't request this, you can safely ignore this email.

Love,
PinkCycle 🩷
"""

  message = MIMEText(body)
  message["to"] = to_email
  message["from"] = GMAIL_SENDER
  message["subject"] = "PinkCycle password reset"

  encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
  send_body = {"raw": encoded_message}

  service.users().messages().send(userId="me", body=send_body).execute()
