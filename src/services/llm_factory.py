from openai import OpenAI
import os
from src.core.config import settings

def get_llm_client():
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    if provider == "openai":
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    elif provider == "groq":
        return OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
    # Add more providers as needed
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_completion(prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
    client = get_llm_client()
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    if provider == "openai":
        model = os.getenv("LLM_MODEL", "gpt-4-turbo")
    else:
        model = os.getenv("LLM_MODEL", "llama3-8b-8192")
        
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM generation failed: {e}")
        return ""
