"""Состояния FSM для регистрации пользователя."""

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    """Состояния процесса регистрации."""
    names = State()  # Ввод ФИО
    group = State()  # Выбор группы
