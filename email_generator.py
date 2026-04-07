"""
email_generator.py
------------------
Uses Groq API (Llama 3 8B) to generate personalized cold emails.
Falls back to a strong template if the API fails.
"""
import requests
import random
from config import settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}

# Small pool of style tweaks to keep each email slightly unique
_OPENERS = [
    "Hope this finds you well.",
    "Reaching out with a quick note.",
    "I'll keep this brief.",
    "Just a short intro from our side.",
]


def _groq_generate(prompt: str, max_tokens: int = 180) -> str:
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.75,
    }
    try:
        resp = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        print(f"Groq API error: {e}")
    except Exception as e:
        print(f"Groq request failed: {e}")
    return ""


def _fallback_email(lead) -> str:
    """Strong template fallback when API is unavailable."""
    opener = random.choice(_OPENERS)
    services_map = {
        "cgi": "photorealistic CGI",
        "compositing": "seamless compositing",
        "3d": "full 3D animation",
        "animation": "character animation",
        "vfx": "premium VFX",
    }
    service_key = next((k for k in services_map if k in lead["service_needed"].lower()), "vfx")
    service_label = services_map[service_key]

    return (
        f"Hi {lead['name']},\n\n"
        f"{opener} I noticed {lead['company']} produces cutting-edge work and wanted to reach out.\n\n"
        f"Our VFX studio specialises in {service_label} and {lead['service_needed']} — we'd love to help elevate "
        f"your next project. Would a quick 15-minute call this week work for you?\n\n"
        f"Best,\nThe VFX Team"
    )


def generate_cold_email(lead) -> str:
    """
    Generates a personalised cold email (<80 words) for the given lead dict/Row.
    """
    name = lead["name"]
    company = lead["company"]
    role = lead["role"]
    service = lead["service_needed"]
    opener = random.choice(_OPENERS)

    prompt = (
        f"[INST] Write a cold sales email body (NO subject line) to {name}, {role} at {company}. "
        f"They need help with: {service}. "
        f"You represent a professional VFX studio offering CGI, compositing, and visual effects. "
        f"Rules: under 80 words, start with '{opener}', mention {company} by name, "
        f"include a CTA to schedule a quick call, sound human and not spammy. "
        f"Output ONLY the email body, nothing else. [/INST]"
    )

    body = _groq_generate(prompt, max_tokens=160)

    # Quality check: must have a greeting and reasonable length
    if body and len(body) > 40 and name.split()[0].lower() in body.lower():
        return body

    # Fallback if quality check fails
    return _fallback_email(lead)


def generate_subject_line(lead) -> str:
    """
    Generates a short, non-salesy subject line for the cold email.
    """
    company = lead["company"]
    service = lead["service_needed"]

    prompt = (
        f"[INST] Write ONE short email subject line (max 7 words, no quotes, no punctuation at end) "
        f"for a cold email to a company called {company} about {service}. "
        f"Make it curious and non-salesy. Output only the subject line. [/INST]"
    )

    subject = _groq_generate(prompt, max_tokens=20)
    subject = subject.split("\n")[0].strip().replace('"', "").replace("Subject:", "").strip()

    if subject and 4 < len(subject) < 80:
        return subject

    return f"Quick question for {company}"
