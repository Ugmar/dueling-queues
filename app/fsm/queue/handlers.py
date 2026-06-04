"""Обработчики для работы с очередями."""

from aiogram import F, types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Room
from app.database.orm_query import (
    get_student_by_tg_id,
    get_object_by_id,
    get_queue_by_room_with_students,
    get_questions_count_by_room,
    get_questions_by_room,
    add_student_to_queue,
    remove_student_from_queue,
    get_queue_position_by_student_and_room,
    is_admin,
    create_object,
    get_room_by_name_and_group,
)
from app.keyboards.keyboards import get_rooms_keyboard, get_queue_keyboard
from .states import AddRoom


queue_router = Router()


async def show_room_queue_by_id(message_or_callback, id_room: int, session: AsyncSession):
    """Вспомогательная функция для отображения очереди по room_id."""
    user_id = message_or_callback.from_user.id

    student = await get_student_by_tg_id(session, user_id)

    if not student or not student.group:
        await message_or_callback.answer("Сначала зарегистрируйтесь через /reg!")
        return

    room = await get_object_by_id(session, Room, id_room)

    if not room:
        await message_or_callback.answer("Комната не найдена!")
        return

    queue_with_students = await get_queue_by_room_with_students(session, room.id)

    # Формируем список очереди (отсортирована по очкам DESC, затем по позиции)
    queue_text = f"📚 Очередь {room.name} (группа {student.group.name}):\n\n"

    if not queue_with_students:
        queue_text += "Очередь пуста. Будьте первым!"
    else:
        for i, queue in enumerate(queue_with_students, 1):
            queue_text += f"{i}. {queue.student.name} - {queue.points} 🏆\n"

    # Добавляем информацию о количестве вопросов (материалов)
    try:
        questions_count = await get_questions_count_by_room(session, room.id)
        queue_text += f"\n📖 Вопросов для самопроверки: {questions_count}"
    except Exception:
        pass

    # Получаем клавиатуру
    keyboard = await get_queue_keyboard(user_id, room.id, session)
    if not keyboard:
        return

    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(queue_text, reply_markup=keyboard)
    else:
        await message_or_callback.message.edit_text(queue_text, reply_markup=keyboard)


@queue_router.message(Command("rooms"))
async def show_rooms(message: types.Message, session: AsyncSession):
    """Показать список комнат для группы студента."""
    user_id = message.from_user.id

    student = await get_student_by_tg_id(session, user_id)
    if not student or not student.group:
        await message.answer("Сначала зарегистрируйтесь через /reg!")
        return

    keyboard = await get_rooms_keyboard(user_id, session)
    if not keyboard:
        await message.answer("Ошибка: не удалось создать клавиатуру")
        return

    await message.answer(
        f"🏫 Очереди для группы {student.group.name}:\nВыберите предмет:",
        reply_markup=keyboard
    )


@queue_router.callback_query(F.data == "rooms_add")
async def start_add_room(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Старт добавления комнаты (только для админов)."""
    user_id = callback.from_user.id
    if not await is_admin(session, user_id):
        await callback.answer("Только для админов", show_alert=True)
        return

    student = await get_student_by_tg_id(session, user_id)
    if not student or not student.group:
        await callback.answer("Сначала зарегистрируйтесь", show_alert=True)
        return

    await state.update_data(group_id=student.group.id)
    await callback.message.edit_text("Введите название новой комнаты:")
    await state.set_state(AddRoom.waiting_name)


@queue_router.message(StateFilter(AddRoom.waiting_name), F.text)
async def add_room_finish(message: types.Message, state: FSMContext, session: AsyncSession):
    """Создание комнаты после ввода названия."""
    room_name = message.text.strip()
    if not room_name:
        await message.answer("Название не может быть пустым. Введите снова:")
        return

    data = await state.get_data()
    group_id = data.get("group_id")
    if not group_id:
        await message.answer("Неизвестная группа. Попробуйте снова.")
        await state.clear()
        return

    existing = await get_room_by_name_and_group(session, room_name, group_id)
    if existing:
        await message.answer("Такая комната уже существует. Введите другое имя:")
        return

    await create_object(session, Room, name=room_name, id_group=group_id)
    await message.answer(f"Комната '{room_name}' создана.")
    await state.clear()

    # Показать обновленный список комнат
    keyboard = await get_rooms_keyboard(message.from_user.id, session)
    if keyboard:
        await message.answer("Обновленный список комнат:", reply_markup=keyboard)


@queue_router.callback_query(F.data.startswith("queue_"))
async def handle_queue_actions(callback: types.CallbackQuery, session: AsyncSession):
    """Обработка действий с очередью (вход/выход)."""
    parts = callback.data.split("_")

    if len(parts) < 3:
        await callback.answer("Неверный формат команды", show_alert=True)
        return

    action = parts[1]  # "join" или "leave"
    room_id = int(parts[2])

    user_id = callback.from_user.id

    student = await get_student_by_tg_id(session, user_id)
    if not student or not student.group:
        await callback.answer("Сначала зарегистрируйтесь!", show_alert=True)
        return

    room = await get_object_by_id(session, Room, room_id)

    if not room:
        await callback.answer("Комната не найдена!", show_alert=True)
        return

    if action == "join":
        # Проверяем, не в очереди ли уже
        existing_queue = await get_queue_position_by_student_and_room(session, student.id, room.id)
        if existing_queue:
            await callback.answer("Вы уже в очереди!", show_alert=True)
            return

        # Добавляем в очередь
        await add_student_to_queue(session, student.id, room.id)
        await callback.answer("Вы добавлены в очередь!")

    elif action == "leave":
        # Удаляем из очереди в БД
        success = await remove_student_from_queue(session, student.id, room.id)
        if success:
            await callback.answer("Вы удалены из очереди!")
        else:
            await callback.answer("Вы не были в очереди!", show_alert=True)

    # Показываем обновленную очередь
    await show_room_queue_by_id(callback, room.id, session)


@queue_router.callback_query(F.data.startswith("rooms_"))
async def show_room_queue(callback: types.CallbackQuery, session: AsyncSession):
    """Показать очередь конкретной комнаты."""
    parts = callback.data.split("_")

    if len(parts) < 2:
        await callback.answer("Неверный формат команды", show_alert=True)
        return

    room_id = int(parts[1])
    await show_room_queue_by_id(callback, room_id, session)


@queue_router.callback_query(F.data.startswith("questions_list_"))
async def show_questions_list(callback: types.CallbackQuery, session: AsyncSession):
    """Показать администратору список вопросов комнаты отдельным сообщением."""
    user_id = callback.from_user.id
    if not await is_admin(session, user_id):
        await callback.answer("Только для админов", show_alert=True)
        return

    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("Неверный формат команды", show_alert=True)
        return

    try:
        room_id = int(parts[2])
    except ValueError:
        await callback.answer("Неверный идентификатор комнаты", show_alert=True)
        return

    room = await get_object_by_id(session, Room, room_id)
    if not room:
        await callback.answer("Комната не найдена!", show_alert=True)
        return

    questions = await get_questions_by_room(session, room_id)
    if not questions:
        await callback.message.answer("В этой комнате пока нет вопросов.")
        await callback.answer()
        return

    # Формируем текстовый список вопросов
    lines = ["📖 Вопросы:"]
    for idx, q in enumerate(questions, start=1):
        # Берем только текст вопроса
        lines.append(f"{idx}. {q.text}")

    text = "\n".join(lines)
    # Отправляем отдельным сообщением, не меняя основное
    await callback.message.answer(text)
    await callback.answer()


@queue_router.callback_query(F.data == "back_to_rooms")
async def back_to_rooms(callback: types.CallbackQuery, session: AsyncSession):
    """Вернуться к списку комнат."""
    user_id = callback.from_user.id

    student = await get_student_by_tg_id(session, user_id)
    if not student or not student.group:
        await callback.answer("Сначала зарегистрируйтесь!", show_alert=True)
        return

    keyboard = await get_rooms_keyboard(user_id, session)
    if not keyboard:
        await callback.message.edit_text("Для вашей группы пока нет комнат.")
        return

    await callback.message.edit_text(
        f"🏫 Очереди для группы {student.group.name}:\nВыберите предмет:",
        reply_markup=keyboard
    )
