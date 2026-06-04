from pydantic import ValidationError
from ollama import AsyncClient

# Handle both package import and direct script execution
try:
    from .schemas import QuizResponse
    from .config import OLLAMA_HOST, OLLAMA_API_KEY, model, prompt
    from .utils import clean_llm_output, url_to_text, pdf_to_text
except ImportError:
    from schemas import QuizResponse
    from config import OLLAMA_HOST, OLLAMA_API_KEY, model, prompt
    from utils import clean_llm_output, url_to_text, pdf_to_text


async def generate_quiz_from_text(text: str) -> QuizResponse | None:
    """
    Generate quiz questions from text using Ollama LLM.

    Args:
        text: Source text for quiz generation

    Returns:
        QuizResponse object with validated quiz questions or None on error
    """
    if not text or not text.strip():
        return None

    if not OLLAMA_API_KEY:
        return None

    client = AsyncClient(
        host=OLLAMA_HOST,
        headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
    )

    try:
        full_prompt = prompt.replace("<<TEXT>>", text)

        response = await client.chat(
            model=model,
            messages=[{"role": "user", "content": full_prompt}],
            format=QuizResponse.model_json_schema(),
            options={
                "temperature": 0.25,  # Low temperature for consistent output
                "top_p": 0.9,  # Nucleus sampling threshold
                "repeat_penalty": 1.1  # Penalty for repeating tokens
            },
        )

        raw = response["message"]["content"]
        clean = clean_llm_output(raw)
        quiz = QuizResponse.model_validate_json(clean)

        return quiz

    except ValidationError as e:
        print(f"Pydantic validation error: {e}")
        return None

    except Exception as e:
        print(f"Ollama API error: {e}")
        return None


async def generate_quiz_from_url(url: str) -> QuizResponse | None:
    """
    Generate quiz questions from URL content.

    Args:
        url: URL to extract text from

    Returns:
        QuizResponse object with validated quiz questions or None on error
    """
    text = await url_to_text(url)
    if not text:
        return None
    return await generate_quiz_from_text(text)


async def generate_quiz_from_pdf(pdf_path: str) -> QuizResponse | None:
    """
    Generate quiz questions from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        QuizResponse object with validated quiz questions or None on error
    """
    text = await pdf_to_text(pdf_path)
    if not text:
        return None
    return await generate_quiz_from_text(text)

if __name__ == "__main__":
    import asyncio

    text = "История Linux, его развитие, проблемы"

    result = asyncio.run(generate_quiz_from_text(text))
    if result:
        print(f"Successfully generated quiz with {len(result.quiz)} questions")
        print(result.model_dump())
    else:
        print("Quiz generation returned empty result")
