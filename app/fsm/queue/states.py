"""Состояния FSM для работы с комнатами/очередями."""

from aiogram.fsm.state import State, StatesGroup


class AddRoom(StatesGroup):
    """Процесс добавления новой комнаты админом."""
    waiting_name = State()  # Ожидание ввода названия комнаты
