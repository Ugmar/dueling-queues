"""Состояния FSM для добавления материалов (генерации вопросов)."""

from aiogram.fsm.state import State, StatesGroup


class AddMaterial(StatesGroup):
    """Состояния процесса добавления материала для генерации квиза."""
    choosing_type = State()  # Выбор типа материала (PDF/URL/текст)
    waiting_text = State()   # Ожидание текста
    waiting_url = State()    # Ожидание ссылки
    waiting_file = State()   # Ожидание файла
