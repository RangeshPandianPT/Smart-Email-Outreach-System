import os
import json
from src.core.config import settings
from src.core.logger import setup_logger

logger = setup_logger(__name__)

def validate_gmail_credentials():
    """
    Validates that Gmail API credentials are correctly configured
    for both local development and headless production environments.
    """
    # In a headless/production environment (like Render), we expect JSON content in env vars.
    if settings.is_headless():
        logger.info("Headless environment detected. Validating Gmail env vars.")
        if not settings.GMAIL_CREDENTIALS_JSON:
            logger.error("Validation Error: GMAIL_CREDENTIALS_JSON is not set.")
            return False
        if not settings.GMAIL_TOKEN_JSON:
            logger.error("Validation Error: GMAIL_TOKEN_JSON is not set.")
            return False
        try:
            json.loads(settings.GMAIL_CREDENTIALS_JSON)
            logger.info("GMAIL_CREDENTIALS_JSON is valid JSON.")
        except json.JSONDecodeError:
            logger.error("Validation Error: GMAIL_CREDENTIALS_JSON is not valid JSON.")
            return False
        try:
            json.loads(settings.GMAIL_TOKEN_JSON)
            logger.info("GMAIL_TOKEN_JSON is valid JSON.")
        except json.JSONDecodeError:
            logger.error("Validation Error: GMAIL_TOKEN_JSON is not valid JSON.")
            return False
    # In a local/development environment, we expect file paths.
    else:
        logger.info("Local environment detected. Validating Gmail file paths.")
        creds_path = settings.GCP_CREDENTIALS_PATH
        token_path = settings.GMAIL_TOKEN_PATH

        if not os.path.exists(creds_path):
            logger.error(f"Validation Error: GCP_CREDENTIALS_PATH file not found at '{creds_path}'.")
            return False
        else:
            logger.info(f"GCP_CREDENTIALS_PATH ('{creds_path}') exists.")

        if not os.path.exists(token_path):
            logger.warning(f"GMAIL_TOKEN_PATH file not found at '{token_path}'.")
            logger.warning("This is normal on first run. The app will create it after authentication.")
        else:
            logger.info(f"GMAIL_TOKEN_PATH ('{token_path}') exists.")

    logger.info("Gmail credential configuration appears valid.")
    return True