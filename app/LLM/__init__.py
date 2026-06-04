"""LLM-based quiz generation module using Ollama."""

from .llm import (
    generate_quiz_from_text,
    generate_quiz_from_url,
    generate_quiz_from_pdf
)
from .schemas import QuizItem, QuizResponse

__all__ = [
    'generate_quiz_from_text',
    'generate_quiz_from_url',
    'generate_quiz_from_pdf',
    'QuizItem',
    'QuizResponse',
]
