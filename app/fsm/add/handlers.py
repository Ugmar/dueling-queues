"""Обработчики для добавления материалов и генерации вопросов."""

from pathlib import Path
import os

from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.orm_query import (
    is_admin,
    bulk_create_questions,
)
from app.LLM.llm import generate_quiz_from_text, generate_quiz_from_url, generate_quiz_from_pdf
from .states import AddMaterial


add_material_router = Router()


@add_material_router.message(Command("cancel"), StateFilter(AddMaterial))
async def cancel_material_add(message: types.Message, state: FSMContext, session: AsyncSession):
    """Отмена добавления материала."""
    data = await state.get_data()
    room_id = data.get('room_id')
    await message.answer("❌ Добавление материала отменено")

    if room_id:
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from app.fsm.queue.handlers import show_room_queue_by_id
        await show_room_queue_by_id(message, room_id, session)

    await state.clear()


@add_material_router.callback_query(F.data.startswith("add_material_"))
async def start_add_material(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начало процесса добавления материала (только для админов)."""
    try:
        room_id = int(callback.data.split("_")[2])
    except Exception:
        await callback.answer("Неверный формат", show_alert=True)
        return

    if not await is_admin(session, callback.from_user.id):
        await callback.answer("Доступ только для админов", show_alert=True)
        return

    await state.update_data(room_id=room_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Файл (PDF)", callback_data="material_type_file")
    builder.button(text="🔗 Ссылка", callback_data="material_type_url")
    builder.button(text="📝 Текст", callback_data="material_type_text")
    builder.button(text="⬅️ Назад", callback_data=f"rooms_{room_id}")
    builder.adjust(1)

    await callback.message.edit_text(
        "📚 Добавление материала\nВыберите источник:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AddMaterial.choosing_type)


@add_material_router.callback_query(AddMaterial.choosing_type, F.data.startswith("material_type_"))
async def choose_material_type(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа материала."""
    material_type = callback.data.split("_")[2]

    if material_type == "file":
        await callback.message.edit_text(
            "📤 Отправьте PDF файл с материалом (<= 20MB).\nДля отмены /cancel"
        )
        await state.set_state(AddMaterial.waiting_file)
    elif material_type == "url":
        await callback.message.edit_text(
            "🔗 Отправьте ссылку на материал (http/https).\nДля отмены /cancel"
        )
        await state.set_state(AddMaterial.waiting_url)
    elif material_type == "text":
        await callback.message.edit_text(
            "📝 Отправьте текст материала (рекомендуемо 500-5000 символов).\nДля отмены /cancel"
        )
        await state.set_state(AddMaterial.waiting_text)


@add_material_router.message(AddMaterial.waiting_file, F.document)
async def receive_file_material(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    """Получение и обработка PDF файла."""
    document = message.document
    if not document.file_name.lower().endswith('.pdf'):
        await message.answer("⚠️ Поддерживаются только PDF файлы")
        return

    data = await state.get_data()
    room_id = data.get('room_id')
    await message.answer("🧠 Обрабатываю материал и генерирую вопросы…")

    temp_dir = Path("temp_files")
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / f"{message.from_user.id}_{document.file_name}"

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        await bot.download(document, destination=file_path)
        if not file_path.exists():
            await message.answer("❌ Не удалось скачать файл")
            return

        quiz = await generate_quiz_from_pdf(str(file_path))
        await _persist_quiz_to_db(session, room_id, quiz)

        if quiz and quiz.quiz:
            await message.answer(f"✅ Добавлено {len(quiz.quiz)} вопросов")
        else:
            await message.answer("⚠️ Не удалось сгенерировать вопросы")
    finally:
        try:
            os.remove(file_path)
        except Exception:
            pass

    from app.fsm.queue.handlers import show_room_queue_by_id
    await show_room_queue_by_id(message, room_id, session)
    await state.clear()


@add_material_router.message(AddMaterial.waiting_url, F.text)
async def receive_url_material(message: types.Message, state: FSMContext, session: AsyncSession):
    """Получение ссылки на материал."""
    url = message.text.strip()
    if not (url.startswith('http://') or url.startswith('https://')):
        await message.answer("⚠️ Ссылка должна начинаться с http:// или https://")
        return

    data = await state.get_data()
    room_id = data.get('room_id')
    await message.answer("🧠 Обрабатываю ссылку и генерирую вопросы…")

    quiz = await generate_quiz_from_url(url)
    await _persist_quiz_to_db(session, room_id, quiz)

    if quiz and quiz.quiz:
        await message.answer(f"✅ Добавлено {len(quiz.quiz)} вопросов")
    else:
        await message.answer("⚠️ Не удалось сгенерировать вопросы")

    from app.fsm.queue.handlers import show_room_queue_by_id
    await show_room_queue_by_id(message, room_id, session)
    await state.clear()


@add_material_router.message(AddMaterial.waiting_text, F.text)
async def receive_text_material(message: types.Message, state: FSMContext, session: AsyncSession):
    """Получение текста материала."""
    text_for_quiz = message.text.strip()
    data = await state.get_data()
    room_id = data.get('room_id')
    await message.answer("🧠 Обрабатываю текст и генерирую вопросы…")

    quiz = await generate_quiz_from_text(text_for_quiz)
    await _persist_quiz_to_db(session, room_id, quiz)

    if quiz and quiz.quiz:
        await message.answer(f"✅ Добавлено {len(quiz.quiz)} вопросов")
    else:
        await message.answer("⚠️ Не удалось сгенерировать вопросы")

    from app.fsm.queue.handlers import show_room_queue_by_id
    await show_room_queue_by_id(message, room_id, session)
    await state.clear()


async def _persist_quiz_to_db(session: AsyncSession, room_id: int, quiz) -> None:
    """Сохранить результаты генерации квиза как вопросы комнаты."""
    if not quiz or not getattr(quiz, 'quiz', None):
        return
    questions_payload = []
    for item in quiz.quiz:
        questions_payload.append({
            'text': item.question,
            'wrong_answer1': item.wrong_answers[0],
            'wrong_answer2': item.wrong_answers[1],
            'wrong_answer3': item.wrong_answers[2],
            'correct_answer': item.correct_answer,
        })
    await bulk_create_questions(session, room_id, questions_payload)
