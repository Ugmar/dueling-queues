"""Utilities for quiz functionality."""

import random
from typing import Tuple, List
from app.database.models import Question
from .config import QUIZ_QUESTIONS_COUNT


def shuffle_answers(question: Question) -> Tuple[List[str], int]:
    """
    Shuffle the 4 answer options and return them with the index of the correct answer.

    Args:
        question: Question object with correct and wrong answers

    Returns:
        Tuple of (shuffled_answers_list, correct_answer_index)
    """
    answers = [
        question.correct_answer,
        question.wrong_answer1,
        question.wrong_answer2,
        question.wrong_answer3
    ]

    # Shuffle the list
    random.shuffle(answers)

    # Find the index of the correct answer in the shuffled list
    correct_index = answers.index(question.correct_answer)

    return answers, correct_index


def format_question_message(question: Question, shuffled_answers: List[str],
                            question_number: int, total_questions: int = QUIZ_QUESTIONS_COUNT) -> str:
    """
    Format question message with answers.

    Args:
        question: Question object
        shuffled_answers: List of 4 shuffled answers
        question_number: Current question number (1-indexed)
        total_questions: Total number of questions in quiz

    Returns:
        Formatted message text
    """
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

    lines = [
        f"Вопрос {question_number}/{total_questions}\n",
        question.text,
        ""
    ]

    for emoji, answer in zip(emojis, shuffled_answers):
        lines.append(f"{emoji} {answer}")

    return "\n".join(lines)
