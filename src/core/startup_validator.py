"""
Startup validation module - checks Gmail credentials, environment setup, and database readiness on app launch.
Provides clear error messages for configuration issues in production environments.
"""
import os
import json
from src.core.logger import setup_logger
from src.core.config import settings

logger = setup_logger("startup_validator")


def validate_gmail_credentials() -> tuple[bool, str]:
    """
    Validates that Gmail credentials are properly configured.
    Returns (is_valid, message)
    """
    is_headless = bool(
        os.getenv("RENDER_SERVICE_ID") or 
        os.getenv("RENDER") == "true" or 
        settings.APP_ENV.lower() in {"production", "prod"}
    )
    
    # Check for JSON token in environment
    if settings.GMAIL_TOKEN_JSON.strip():
        try:
            json.loads(settings.GMAIL_TOKEN_JSON.strip())
            logger.info("✓ Gmail token loaded from GMAIL_TOKEN_JSON environment variable")
            return True, "Gmail token configured via env"
        except json.JSONDecodeError as e:
            return False, f"GMAIL_TOKEN_JSON contains invalid JSON: {e}"
    
    # Check for token file
    token_path = settings.GMAIL_TOKEN_PATH
    if not os.path.isabs(token_path):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        token_path = os.path.join(repo_root, token_path)
    
    if os.path.exists(token_path):
        try:
            with open(token_path) as f:
                json.load(f)
            logger.info(f"✓ Gmail token found at {token_path}")
            return True, "Gmail token file exists"
        except (json.JSONDecodeError, OSError) as e:
            return False, f"Gmail token file at {token_path} is corrupted: {e}"
    
    # Check for credentials JSON
    if settings.GMAIL_CREDENTIALS_JSON.strip():
        try:
            json.loads(settings.GMAIL_CREDENTIALS_JSON.strip())
            logger.info("✓ Gmail credentials loaded from GMAIL_CREDENTIALS_JSON environment variable")
            return True, "Gmail credentials configured via env"
        except json.JSONDecodeError as e:
            return False, f"GMAIL_CREDENTIALS_JSON contains invalid JSON: {e}"
    
    # Check for credentials file
    creds_path = settings.GCP_CREDENTIALS_PATH
    if not os.path.isabs(creds_path):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        creds_path = os.path.join(repo_root, creds_path)
    
    if os.path.exists(creds_path):
        logger.info(f"✓ Gmail credentials file found at {creds_path}")
        return True, "Gmail credentials file exists"
    
    # No credentials found
    if is_headless:
        return False, (
            "HEADLESS RUNTIME - No valid Gmail credentials found.\n"
            "To fix:\n"
            "  1. Set GMAIL_TOKEN_JSON to your token.json content (base64 encoded or raw JSON)\n"
            "  2. OR set GMAIL_CREDENTIALS_JSON to your credentials.json content\n"
            "  3. OR mount token.json file and set GMAIL_TOKEN_PATH environment variable\n"
            "See README for detailed setup instructions."
        )
    else:
        logger.info("No Gmail credentials found. Will authenticate on first use (browser will open).")
        return True, "Will authenticate on first use"


def validate_api_keys() -> tuple[bool, str]:
    """
    Validates that required API keys are configured.
    Returns (is_valid, message)
    """
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key":
        logger.warning("⚠ GROQ_API_KEY not set - email generation will fail")
        return False, "GROQ_API_KEY not configured in environment"
    
    logger.info("✓ GROQ_API_KEY configured")
    return True, "API keys configured"


def validate_database() -> tuple[bool, str]:
    """
    Validates that database can be accessed and initialized.
    Returns (is_valid, message)
    """
    try:
        from src.core.database import init_db, get_db_connection
        init_db()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leads")
            count = cursor.fetchone()[0]
        logger.info(f"✓ Database initialized with {count} leads")
        return True, "Database ready"
    except Exception as e:
        return False, f"Database error: {e}"


def run_startup_checks():
    """
    Runs all startup validation checks.
    Logs results and raises RuntimeError if critical issues found.
    """
    logger.info("=" * 60)
    logger.info("Running startup validation checks...")
    logger.info("=" * 60)
    
    checks = [
        ("Gmail Credentials", validate_gmail_credentials),
        ("API Keys", validate_api_keys),
        ("Database", validate_database),
    ]
    
    failures = []
    for check_name, check_fn in checks:
        try:
            is_valid, message = check_fn()
            status = "✓" if is_valid else "✗"
            logger.info(f"{status} {check_name}: {message}")
            if not is_valid:
                failures.append((check_name, message))
        except Exception as e:
            logger.error(f"✗ {check_name} check failed: {e}")
            failures.append((check_name, str(e)))
    
    logger.info("=" * 60)
    
    if failures:
        error_msg = "Startup validation failed:\n"
        for check_name, message in failures:
            error_msg += f"\n{check_name}:\n  {message}\n"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("✓ All startup checks passed!")
    logger.info("=" * 60)
