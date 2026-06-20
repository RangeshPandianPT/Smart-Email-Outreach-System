"""
classifier.py
-------------
Classifies email reply text into one of four categories using
Groq LLM API. Falls back to keyword matching.
"""
from src.core.config import settings
from src.services.llm_factory import generate_completion

LABELS = ["Interested", "Not Interested", "Meeting Request", "Neutral", "Bounce", "Out of Office"]

# Keyword fallback mapping
_KEYWORDS = {
    "Meeting Request": ["schedule", "call", "meeting", "calendar", "available", "book", "zoom", "teams", "let's talk"],
    "Not Interested": ["not interested", "unsubscribe", "remove", "stop", "don't contact", "no thank", "opt out"],
    "Interested": ["tell me more", "sounds good", "interested", "portfolio", "pricing", "rates", "love to", "would like"],
    "Bounce": ["postmaster", "mailer-daemon", "delivery failed", "undeliverable", "address not found", "user unknown", "bounced"],
    "Out of Office": ["out of office", "out of the office", "vacation", "away from my desk", "ooo", "auto-reply", "auto reply", "automated response"],
}


def classify_reply(email_text: str) -> str:
    """
    Classifies a reply email into: Interested, Not Interested, Meeting Request, or Neutral.
    Uses LLM classification first, then keyword fallback.
    """
    # Truncate to 512 chars for the model
    truncated = email_text[:512].strip()

    try:
        prompt = (
            f"Classify the following email reply into exactly one of these labels: {', '.join(LABELS)}.\n"
            f"Reply:\n{truncated}\n"
            f"Output ONLY the label, nothing else."
        )
        best_label = generate_completion(prompt, max_tokens=10, temperature=0.0)

        if best_label:
            for label in LABELS:
                if label.lower() in best_label.lower():
                    print(f"  Classification: '{label}' (LLM)")
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
