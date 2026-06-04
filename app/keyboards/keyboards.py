from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Group, Room
from app.database.orm_query import (
    get_all_objects,
    get_student_by_tg_id,
    get_rooms_by_group,
    get_queue_position_by_student_and_room,
    get_queue_count_students,
    is_admin,
    get_questions_count_by_room,
)
from app.fsm.quiz.config import QUIZ_QUESTIONS_COUNT


async def get_groups_keyboard(session: AsyncSession) -> types.InlineKeyboardMarkup | None:
    """Клавиатура для выбора группы при регистрации (из БД)."""
    groups = await get_all_objects(session, Group)
    if not groups:
        return None

    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=group.name, callback_data=f"group_{group.id}")
    builder.adjust(2, 2, 2)
    return builder.as_markup()


async def get_rooms_keyboard(user_id: int, session: AsyncSession) -> types.InlineKeyboardMarkup | None:
    """Клавиатура выбора комнаты для группы студента (из БД)."""
    student = await get_student_by_tg_id(session, user_id)
    if not student or not student.id_group:
        return None

    rooms = await get_rooms_by_group(session, student.id_group)
    admin = await is_admin(session, user_id)

    builder = InlineKeyboardBuilder()
    if rooms:
        for room in rooms:
            count = await get_queue_count_students(session, room.id)
            builder.button(text=f"{room.name} ({count} чел.)",
                           callback_data=f"rooms_{room.id}")

    # Кнопка добавления комнаты только для админа (даже если комнат нет)
    if admin:
        builder.button(text="➕ Добавить комнату", callback_data="rooms_add")

    if not rooms and not admin:
        return None

    builder.adjust(1)
    return builder.as_markup()


async def get_queue_keyboard(user_id: int, room_id: int, session: AsyncSession) -> types.InlineKeyboardMarkup | None:
    """Клавиатура управления очередью для комнаты (войти/выйти)."""
    student = await get_student_by_tg_id(session, user_id)
    if not student:
        return None

    queue_item = await get_queue_position_by_student_and_room(session, student.id, room_id)
    is_in_queue = queue_item is not None
    admin = await is_admin(session, user_id)

    builder = InlineKeyboardBuilder()
    if is_in_queue:
        builder.button(text="❌ Выйти из очереди",
                       callback_data=f"queue_leave_{room_id}")
    else:
        builder.button(text="✅ Добавиться в очередь",
                       callback_data=f"queue_join_{room_id}")

    # Показать количество вопросов только админу и дать кнопку добавления материала
    if admin:
        try:
            qcount = await get_questions_count_by_room(session, room_id)
            queue_count = await get_queue_count_students(session, room_id)

            # Show questions button
            builder.button(
                text=f"📖 Вопросов: {qcount}", callback_data=f"questions_list_{room_id}")

            # Show start quiz button only if >= 10 questions and >= 1 participant
            if qcount >= QUIZ_QUESTIONS_COUNT and queue_count >= 1:
                builder.button(text="🎯 Запустить квиз",
                               callback_data=f"start_quiz_{room_id}")
        except Exception:
            pass
        builder.button(text="📚 Добавить материал",
                       callback_data=f"add_material_{room_id}")

    builder.button(text="⬅️ Назад к очередям", callback_data="back_to_rooms")
    builder.adjust(1, 1, 1)
    return builder.as_markup()
