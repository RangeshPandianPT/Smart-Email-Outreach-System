"""
classifier.py
-------------
Classifies email reply text into one of four categories using
Groq LLM API. Falls back to keyword matching.
"""
import requests
from src.core.config import settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}

LABELS = ["Interested", "Not Interested", "Meeting Request", "Neutral"]

# Keyword fallback mapping
_KEYWORDS = {
    "Meeting Request": ["schedule", "call", "meeting", "calendar", "available", "book", "zoom", "teams", "let's talk"],
    "Not Interested": ["not interested", "unsubscribe", "remove", "stop", "don't contact", "no thank", "opt out"],
    "Interested": ["tell me more", "sounds good", "interested", "portfolio", "pricing", "rates", "love to", "would like"],
}


def classify_reply(email_text: str) -> str:
    """
    Classifies a reply email into: Interested, Not Interested, Meeting Request, or Neutral.
    Uses Groq LLM classification first, then keyword fallback.
    """
    # Truncate to 512 chars for the model
    truncated = email_text[:512].strip()

    try:
        prompt = (
            f"Classify the following email reply into exactly one of these labels: {', '.join(LABELS)}.\n"
            f"Reply:\n{truncated}\n"
            f"Output ONLY the label, nothing else."
        )
        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 10,
        }
        resp = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "choices" in data and len(data["choices"]) > 0:
            best_label = data["choices"][0]["message"]["content"].strip()
            for label in LABELS:
                if label.lower() in best_label.lower():
                    print(f"  Classification: '{label}' (Groq)")
                    return label

    except Exception as e:
        print(f"Groq classifier error: {e}, falling back to keyword matching.")

    # Keyword fallback
    text_lower = email_text.lower()
    for label, keywords in _KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            print(f"  Classification (keyword): '{label}'")
            return label

    return "Neutral"
