"""
LLM factory — returns configured Groq / Gemini / OpenAI clients.
All agents import from here so we switch models in one place.
"""

from functools import lru_cache
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings


@lru_cache()
def get_groq_llm(model: str = None, temperature: float = 0.3):
    """Primary LLM: Groq llama-3.3-70b — fast reasoning agent calls."""
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=model or settings.GROQ_MODEL,
        temperature=temperature,
        streaming=True,
    )


@lru_cache()
def get_groq_fast_llm(temperature: float = 0.1):
    """Lightweight Groq model for simple classification/routing tasks."""
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_FAST_MODEL,
        temperature=temperature,
        streaming=False,
    )


@lru_cache()
def get_gemini_llm(temperature: float = 0.2):
    """Gemini 1.5 Flash — used for resume analysis (large context)."""
    return ChatGoogleGenerativeAI(
        google_api_key=settings.GOOGLE_API_KEY,
        model=settings.GEMINI_MODEL,
        temperature=temperature,
        streaming=True,
    )
