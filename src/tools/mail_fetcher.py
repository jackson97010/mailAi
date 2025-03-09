from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
import base64
import email
import json
from datetime import datetime, timedelta
from typing import List, Dict

class MailFetcher:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.creds = None
        self.service = None
        self.emails_cache_file = 'emails_cache.json'

    def authenticate(self):
        """Authenticate with Gmail API using credentials.json"""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)

    def save_emails_to_json(self, emails: List[Dict]):
        """Save fetched emails to JSON file"""
        try:
            # Convert datetime objects to string for JSON serialization
            serializable_emails = []
            for email_data in emails:
                email_copy = email_data.copy()
                if isinstance(email_copy.get('date'), datetime):
                    email_copy['date'] = email_copy['date'].isoformat()
                serializable_emails.append(email_copy)

            with open(self.emails_cache_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_emails, f, indent=2, ensure_ascii=False)
            print(f"\nSaved {len(emails)} emails to {self.emails_cache_file}")
        except Exception as e:
            print(f"Error saving emails to JSON: {e}")

    def load_emails_from_json(self) -> List[Dict]:
        """Load emails from JSON cache file"""
        try:
            if os.path.exists(self.emails_cache_file):
                with open(self.emails_cache_file, 'r', encoding='utf-8') as f:
                    emails = json.load(f)
                # Convert date strings back to datetime objects
                for email_data in emails:
                    if isinstance(email_data.get('date'), str):
                        email_data['date'] = datetime.fromisoformat(email_data['date'])
                print(f"\nLoaded {len(emails)} emails from cache")
                return emails
        except Exception as e:
            print(f"Error loading emails from JSON: {e}")
        return []

    def get_emails(self, time_range_hours: int = 24, use_cache: bool = True) -> List[Dict]:
        """Fetch emails from Gmail within the time range or load from cache"""
        # Try to load from cache first if use_cache is True
        if use_cache:
            cached_emails = self.load_emails_from_json()
            if cached_emails:
                return cached_emails

        if not self.service:
            self.authenticate()

        emails = []
        try:
            # Calculate time range
            time_ago = datetime.now() - timedelta(hours=time_range_hours)
            query = f'after:{int(time_ago.timestamp())}'

            # Get messages
            results = self.service.users().messages().list(
                userId='me', q=query).execute()
            messages = results.get('messages', [])

            print(f"\nFetching {len(messages)} emails from Gmail...")
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', id=message['id'], format='full').execute()
                
                # Extract headers
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

                # Get email body
                body = self._get_email_body(msg['payload'])

                emails.append({
                    "subject": subject,
                    "sender": sender,
                    "date": email.utils.parsedate_to_datetime(date),
                    "body": body,
                    "message_id": message['id'],
                    "labels": msg.get('labelIds', [])
                })

            # Save fetched emails to JSON
            self.save_emails_to_json(emails)

        except Exception as e:
            print(f"Error fetching emails: {e}")
            # Try to load from cache as fallback
            if not emails:
                emails = self.load_emails_from_json()

        return emails

    def _get_email_body(self, payload):
        """Extract email body from payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    elif 'parts' in part:
                        return self._get_email_body(part)
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        return "" 