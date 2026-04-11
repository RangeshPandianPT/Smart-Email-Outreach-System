import os
import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.core.config import settings

# If you change these scopes, delete token.json so you re-authenticate.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_credentials_path() -> str:
    """
    Resolves the path to credentials.json.
    Checks the configured path first, then falls back to src/core/credentials.json.
    """
    configured = settings.GCP_CREDENTIALS_PATH
    if os.path.isabs(configured):
        return configured
    # Resolve relative paths from the repository root so docs/.env are intuitive.
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    configured_path = os.path.join(repo_root, configured)
    if os.path.exists(configured_path):
        return configured_path

    # Fallback to src/core/credentials.json
    return os.path.join(repo_root, "src", "core", "credentials.json")


def get_token_path() -> str:
    """Resolves token path from config, defaulting to src/core/token.json."""
    configured = settings.GMAIL_TOKEN_PATH
    if os.path.isabs(configured):
        return configured

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(repo_root, configured)


def _is_headless_runtime() -> bool:
    return bool(os.getenv("RENDER_SERVICE_ID") or os.getenv("RENDER") == "true" or settings.APP_ENV.lower() in {"production", "prod"})


def _load_token_from_env() -> Credentials | None:
    raw_token = settings.GMAIL_TOKEN_JSON.strip()
    if not raw_token:
        return None

    try:
        token_info = json.loads(raw_token)
        return Credentials.from_authorized_user_info(token_info, SCOPES)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid GMAIL_TOKEN_JSON: expected valid JSON.") from exc


def _build_flow(credentials_path: str) -> InstalledAppFlow:
    raw_credentials_json = settings.GMAIL_CREDENTIALS_JSON.strip()
    if raw_credentials_json:
        try:
            client_config = json.loads(raw_credentials_json)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid GMAIL_CREDENTIALS_JSON: expected valid JSON.") from exc
        return InstalledAppFlow.from_client_config(client_config, SCOPES)

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"\n\nERROR: credentials.json not found at '{credentials_path}'\n"
            "Provide GCP_CREDENTIALS_PATH, or set GMAIL_CREDENTIALS_JSON in environment variables.\n"
        )

    return InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)

def get_gmail_service():
    """
    Authenticates with Gmail API using OAuth2.
    On first run, it opens a browser window for you to log in and grant permission.
    Subsequent runs will use the saved token.json automatically.
    """
    creds = _load_token_from_env()
    token_path = get_token_path()
    credentials_path = get_credentials_path()

    # Load existing token if it exists
    if not creds and os.path.exists(token_path):
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
            if _is_headless_runtime():
                raise RuntimeError(
                    "No valid Gmail token found in headless runtime. "
                    "Set GMAIL_TOKEN_JSON (preferred) or mount token file and point GMAIL_TOKEN_PATH to it."
                )

            print(f"Using credentials from: {credentials_path}")
            print("Opening browser for Gmail authentication...")
            flow = _build_flow(credentials_path)
            creds = flow.run_local_server(port=0, prompt='consent')

        # Save the refreshed/new token for future runs
        try:
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            print(f"Token saved to: {token_path}")
        except OSError as e:
            # In ephemeral or read-only runtimes, refresh still works for current process.
            print(f"Warning: could not persist token at '{token_path}': {e}")

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
