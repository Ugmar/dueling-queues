"""Configuration for LLM-based quiz generation."""

import os
from dotenv import load_dotenv

load_dotenv()

# Ollama API configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', "https://ollama.com")
OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')

# Model selection
model = 'deepseek-v3.1:671b-cloud'

# System prompt for quiz generation
prompt = """YOU ARE A STRICT QUIZ GENERATION ENGINE.

TASK:
Generate up to 10 quiz questions based ONLY on the SOURCE TEXT.

ABSOLUTE RULES:

- OUTPUT MUST BE PURE JSON.
- NEVER USE ``` CODE BLOCKS.
- DO NOT wrap JSON in markdown.
- START OUTPUT WITH "{" AND END WITH "}".

ALL content MUST be in RUSSIAN.

NO explanations. NO comments. NO markdown.
NO thinking aloud. NO reasoning shown.

Each question MUST include:
- level
- question
- correct_answer
- wrong_answers (EXACTLY 3 items)

LEVELS:
- low
- middle
- high

STRICT CONTENT RULES:
- No duplicates
- No vague questions
- Only SOURCE TEXT info
- URLs and technical data are FORBIDDEN

JSON FAILSAFE:
If valid JSON is impossible, output exactly: {}

FORBIDDEN QUESTION TYPES:
- Questions about URLs
- Questions about links
- Questions about technical metadata

MANDATORY JSON FORMAT:

{
  "quiz": [
    {
      "level": "low|middle|high",
      "question": "Russian string",
      "correct_answer": "Russian string",
      "wrong_answers": ["Russian string", "Russian string", "Russian string"]
    }
  ]
}

SOURCE TEXT (RUSSIAN):
<<TEXT>>
"""
