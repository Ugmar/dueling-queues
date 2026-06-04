"""Pydantic schemas for quiz generation and validation."""

from pydantic import BaseModel, Field
from typing import Literal


class QuizItem(BaseModel):
    """Single quiz question with multiple choice answers."""

    level: Literal["low", "middle", "high"] = Field(
        description="Difficulty level of the question"
    )
    question: str = Field(
        description="The quiz question text"
    )
    correct_answer: str = Field(
        description="The correct answer to the question"
    )
    wrong_answers: list[str] = Field(
        description="List of exactly 3 incorrect answers",
        min_length=3,
        max_length=3
    )


class QuizResponse(BaseModel):
    """Response containing a list of quiz questions."""

    quiz: list[QuizItem] = Field(
        description="List of quiz questions",
        max_length=10
    )
