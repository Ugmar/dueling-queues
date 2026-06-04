"""FSM states for quiz."""

from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    """Quiz FSM states."""
    waiting_start = State()  # Пользователь получил приглашение, ждёт нажатия "Начать квиз"
    answering = State()      # Пользователь проходит тест (отвечает на вопросы)
