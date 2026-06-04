"""Обработчики регистрации пользователя."""

import re
from aiogram import F, types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Group
from app.database.orm_query import (
    get_student_by_tg_id,
    create_student,
    create_object,
    get_object_by_id,
    get_group_by_name,
    is_admin,
    get_all_objects,
    get_students_with_group,
    get_students_by_group,
    get_rooms_by_group,
)
from app.keyboards.keyboards import get_groups_keyboard
from .states import Registration


reg_router = Router()


@reg_router.message(Command("add_group"))
async def add_group(message: types.Message, session: AsyncSession):
    """Создание новой группы (только для админов)."""
    user_id = message.from_user.id
    if not await is_admin(session, user_id):
        await message.answer("Только для админов")
        return

    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Использование: /add_group <название>")
        return

    group_name = parts[1].strip()
    existing = await get_group_by_name(session, group_name)
    if existing:
        await message.answer("Такая группа уже существует")
        return

    await create_object(session, Group, name=group_name)
    await message.answer(f"Группа '{group_name}' создана")


@reg_router.message(StateFilter(None), Command("reg"))
async def registration(message: types.Message, state: FSMContext, session: AsyncSession):
    """Начало регистрации пользователя."""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли уже в БД
    student = await get_student_by_tg_id(session, user_id)
    if student:
        await message.answer("Вы уже зарегистрированы!")
        return

    await message.answer("Как вас записать? (Фамилия Имя Отчество)")
    await state.set_state(Registration.names)


@reg_router.message(Registration.names, F.text)
async def add_user_name(message: types.Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода ФИО."""
    user_input = message.text.strip()

    pattern = r'^[А-ЯЁ][а-яё]* [А-ЯЁ][а-яё]*( [А-ЯЁ][а-яё]*)*$'

    if not re.match(pattern, user_input):
        await message.answer(
            "Неверный формат имени!\n\n"
            "Введите имя в формате:\n"
            "Фамилия Имя (например: Иванов Иван)\nИли\n"
            "Фамилия Имя Отчество (например: Иванов Иван Иванович)\n\n"
            "Пожалуйста, попробуйте еще раз:"
        )
        return

    await state.update_data(name=user_input)

    keyboard = await get_groups_keyboard(session)

    if not keyboard:
        await message.answer("Нет доступных групп. Обратитесь к администратору.")
        await state.clear()
        return

    await message.answer("Из какой вы группы?", reply_markup=keyboard)
    await state.set_state(Registration.group)


@reg_router.callback_query(Registration.group, F.data.startswith("group_"))
async def process_group_selection(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора группы и завершение регистрации."""
    try:
        group_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Неизвестный ID группы", show_alert=True)
        return

    group = await get_object_by_id(session, Group, group_id)
    if not group:
        await callback.answer("Группа не найдена", show_alert=True)
        return

    data = await state.get_data()
    user_name = data.get('name', 'Неизвестный пользователь')

    student = await create_student(
        session,
        name=user_name,
        tg_id=callback.from_user.id,
        group_id=group.id
    )

    # Проверяем, админ ли это (по БД)
    user_is_admin = await is_admin(session, callback.from_user.id)
    admin_text = "\n👑 Вы администратор!" if user_is_admin else ""

    await callback.message.edit_text(
        f"Регистрация завершена!\n\n"
        f"Имя: {user_name}\n"
        f"Группа: {group.name}"
        f"\n\nТеперь вы можете просмотреть очереди! Команда → /rooms"
        f"{admin_text}"
    )

    await state.clear()


@reg_router.message(StateFilter(None), Command("students"))
async def show_students(message: types.Message, session: AsyncSession):
    """Показать список зарегистрированных студентов."""
    students = await get_students_with_group(session)

    if not students:
        await message.answer("Список студентов пуст!")
        return

    response = "Список зарегистрированных студентов:\n\n"

    for i, student in enumerate(students, 1):
        response += f"👤 Студент №{i}\n"
        response += f"   Имя: {student.name}\n"
        response += f"   Группа: {student.group.name if student.group else 'Не указана'}\n"

    response += f"Всего: {len(students)} студент(ов)"
    await message.answer(response)


@reg_router.message(StateFilter(None), Command("groups"))
async def show_groups(message: types.Message, session: AsyncSession):
    """Показать список всех групп."""
    groups = await get_all_objects(session, Group)

    if not groups:
        await message.answer("Список групп пуст!")
        return

    response = "🏫 Список групп:\n\n"

    for i, group in enumerate(groups, 1):
        students = await get_students_by_group(session, group.id)
        student_count = len(students)

        rooms = await get_rooms_by_group(session, group.id)
        room_count = len(rooms)

        response += f"{i}. {group.name}\n"
        response += f"   👥 Студентов: {student_count}\n"
        response += f"   🏠 Комнат: {room_count}\n\n"

    response += f"📊 Всего: {len(groups)} групп"
    await message.answer(response)
