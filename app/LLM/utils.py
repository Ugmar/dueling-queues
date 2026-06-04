import re
import asyncio
from pathlib import Path

import fitz
import aiohttp
import trafilatura


def clean_llm_output(raw: str) -> str:
    """
    Clean LLM output by removing markdown code blocks and extracting JSON.

    Args:
        raw: Raw output from LLM

    Returns:
        Cleaned JSON string

    Raises:
        ValueError: If no valid JSON object found in output
    """
    # Remove markdown code blocks
    raw = re.sub(r"```[a-zA-Z]*", "", raw)
    raw = raw.replace("```", "").strip()

    # Extract JSON object
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM output")

    return match.group(0)


async def pdf_to_text(pdf_path: str) -> str:
    """
    Extract text from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text from all pages
    """
    path = Path(pdf_path)
    if not path.exists():
        return ""

    if not path.suffix.lower() == '.pdf':
        return ""

    def extract():
        try:
            with fitz.open(pdf_path) as doc:
                pages = []
                for page in doc:
                    text = page.get_text()

                    # Clean extracted text
                    text = text.replace("\x00", "")  # Remove null bytes
                    text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
                    text = text.strip()

                    if text:
                        pages.append(text)

                return "\n".join(pages)
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""

    return await asyncio.to_thread(extract)


async def url_to_text(url: str) -> str:
    """
    Extract text content from URL.

    Args:
        url: URL to extract text from

    Returns:
        Extracted text content
    """
    url = url.strip()

    if not url:
        return ""

    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as response:
                if response.status != 200:
                    print(
                        f"Failed to fetch URL. Status code: {response.status}")
                    return ""

                html = await response.text()

        def extract():
            result = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,  # Important for structured content
                include_links=False,
                include_images=False,
                include_formatting=True,
                output_format='txt',
                favor_recall=True  # Better for complex pages
            )
            return result or ""

        return await asyncio.to_thread(extract)

    except Exception as e:
        print(f"Error processing URL {url}: {str(e)}")
        return ""

if __name__ == "__main__":
    async def main():
        # Avoid circular import by importing only when needed
        try:
            from .llm import generate_quiz_from_text
        except ImportError:
            # Fallback for direct execution
            from llm import generate_quiz_from_text

        # Example: Generate quiz from URL
        url = "https://alexott.net/ru/linux/valgrind/Valgrind.html"
        text = await url_to_text(url)
        quiz = await generate_quiz_from_text(text)
        if quiz:
            print(quiz.model_dump())
        else:
            print("Failed to generate quiz")

    asyncio.run(main())
