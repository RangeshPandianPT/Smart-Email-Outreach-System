import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import settings

# If you change these scopes, delete token.json so you re-authenticate.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_credentials_path() -> str:
    """
    Resolves the path to credentials.json.
    Checks the configured path first, then falls back to the project root.
    """
    configured = settings.GCP_CREDENTIALS_PATH
    if os.path.isabs(configured):
        return configured
    # Resolve relative to this file's directory (project root)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), configured)

def get_gmail_service():
    """
    Authenticates with Gmail API using OAuth2.
    On first run, it opens a browser window for you to log in and grant permission.
    Subsequent runs will use the saved token.json automatically.
    """
    creds = None
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')
    credentials_path = get_credentials_path()

    # Load existing token if it exists
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("Gmail token refreshed successfully.")
            except Exception as e:
                print(f"Token refresh failed: {e}. Re-authenticating...")
                creds = None

        if not creds:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"\n\nERROR: credentials.json not found at '{credentials_path}'\n"
                    "Please ensure the credentials.json file is in the project directory.\n"
                    "Download it from: GCP Console -> APIs & Services -> Credentials -> OAuth 2.0 Client\n"
                )

            print(f"Using credentials from: {credentials_path}")
            print("Opening browser for Gmail authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0, prompt='consent')

        # Save the refreshed/new token for future runs
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"Token saved to: {token_path}")

    service = build('gmail', 'v1', credentials=creds)
    print("Gmail service connected successfully.")
    return service


def test_gmail_connection():
    """
    Simple test: lists your Gmail labels to verify the connection works.
    Run this file directly to test: python gmail_client.py
    """
    try:
        service = get_gmail_service()
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        print(f"\nConnection successful! Found {len(labels)} Gmail labels.")
        for label in labels[:5]:
            print(f"  - {label['name']}")
        return True
    except Exception as e:
        print(f"\nConnection failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Gmail API connection...")
    test_gmail_connection()
