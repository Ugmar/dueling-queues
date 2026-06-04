"""Quiz handlers - quiz flow management."""

from aiogram import F, types, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Room, Question, Queue
from app.database.orm_query import (
    get_student_by_tg_id,
    get_object_by_id,
    get_queue_by_room_with_students,
    get_questions_count_by_room,
    get_random_questions_by_room,
    is_admin,
    reset_quiz_points,
    get_queue_position_by_student_and_room,
)
from app.keyboards.keyboards import get_queue_keyboard
from .states import QuizStates
from .config import QUIZ_QUESTIONS_COUNT
from .utils import shuffle_answers, format_question_message

quiz_router = Router()


@quiz_router.callback_query(F.data.startswith("start_quiz_"))
async def admin_start_quiz(callback: types.CallbackQuery, session: AsyncSession):
    """
    Admin starts a quiz for the room.
    - Check: is admin, >= 10 questions, >= 1 participant
    - Send invitation to all queue participants
    """
    user_id = callback.from_user.id

    # Check if admin
    if not await is_admin(session, user_id):
        await callback.answer("Только для админов", show_alert=True)
        return

    # Parse room_id
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("Неверный формат команды", show_alert=True)
        return

    try:
        room_id = int(parts[2])
    except ValueError:
        await callback.answer("Неверный идентификатор комнаты", show_alert=True)
        return

    # Get room
    room = await get_object_by_id(session, Room, room_id)
    if not room:
        await callback.answer("Комната не найдена!", show_alert=True)
        return

    # Check questions count
    questions_count = await get_questions_count_by_room(session, room_id)
    if questions_count < QUIZ_QUESTIONS_COUNT:
        await callback.answer(
            f"Недостаточно вопросов. Нужно минимум {QUIZ_QUESTIONS_COUNT}, а сейчас {questions_count}",
            show_alert=True
        )
        return

    # Get all queue participants
    queue_participants = await get_queue_by_room_with_students(session, room_id)
    if not queue_participants:
        await callback.answer("В очереди нет участников!", show_alert=True)
        return

    # Reset points for all participants
    await reset_quiz_points(session, room_id)

    # Send invitation to each participant
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Начать квиз", callback_data=f"quiz_join_{room_id}")

    invitation_text = f"🎯 Начался квиз в очереди '{room.name}'!\n\nНажмите на кнопку чтобы начать:"

    for queue_item in queue_participants:
        try:
            await callback.bot.send_message(
                chat_id=queue_item.student.tg_id,
                text=invitation_text,
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            print(
                f"Error sending quiz invite to {queue_item.student.tg_id}: {e}")

    await callback.answer("Квиз запущен! Приглашения отправлены.")


@quiz_router.callback_query(F.data.startswith("quiz_join_"))
async def user_join_quiz_room(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    User joins the quiz for a specific room - get 10 random questions and start.
    """
    user_id = callback.from_user.id

    # Parse room_id
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("Неверный формат команды", show_alert=True)
        return

    try:
        room_id = int(parts[2])
    except ValueError:
        await callback.answer("Неверный идентификатор комнаты", show_alert=True)
        return

    # Get student
    student = await get_student_by_tg_id(session, user_id)
    if not student:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return

    # Get room
    room = await get_object_by_id(session, Room, room_id)
    if not room:
        await callback.answer("Комната не найдена!", show_alert=True)
        return

    # Get 10 random questions
    questions = await get_random_questions_by_room(session, room_id, limit=QUIZ_QUESTIONS_COUNT)
    if len(questions) < QUIZ_QUESTIONS_COUNT:
        await callback.answer(f"Недостаточно вопросов ({len(questions)}/{QUIZ_QUESTIONS_COUNT})", show_alert=True)
        return

    # Store quiz data in FSM state
    question_ids = [q.id for q in questions]
    await state.update_data(
        room_id=room_id,
        room_name=room.name,
        questions_ids=question_ids,
        current_index=0,
        correct_count=0,
    )
    await state.set_state(QuizStates.waiting_start)

    # Send first question
    await send_next_question(callback.message, state, session)
    await state.set_state(QuizStates.answering)


async def send_next_question(message_or_callback, state: FSMContext, session: AsyncSession):
    """
    Send the next question to the user.
    """
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    questions_ids = data.get("questions_ids", [])

    if current_index >= len(questions_ids):
        # Quiz finished
        await finish_quiz(message_or_callback, state, session)
        return

    # Get current question
    question_id = questions_ids[current_index]
    question = await get_object_by_id(session, Question, question_id)
    if not question:
        # Get message object to send error
        msg = message_or_callback.message if isinstance(
            message_or_callback, types.CallbackQuery) else message_or_callback
        await msg.answer("Ошибка: вопрос не найден")
        await state.clear()
        return

    # Shuffle answers and build keyboard
    shuffled_answers, correct_index = shuffle_answers(question)

    # Format message
    message_text = format_question_message(
        question,
        shuffled_answers,
        current_index + 1,
        total_questions=QUIZ_QUESTIONS_COUNT
    )

    # Build keyboard with answer buttons
    builder = InlineKeyboardBuilder()
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

    for idx, answer in enumerate(shuffled_answers):
        # Determine if this is the correct answer
        is_correct = (idx == correct_index)
        # Make each button callback unique by including the index
        callback_data = f"quiz_answer_{idx}_{'correct' if is_correct else 'wrong'}"

        builder.button(
            text=emojis[idx],
            callback_data=callback_data
        )

    builder.adjust(2)  # 2 buttons per row

    # Send or edit message
    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.edit_text(message_text, reply_markup=builder.as_markup())
    else:
        await message_or_callback.edit_text(message_text, reply_markup=builder.as_markup())


@quiz_router.callback_query(
    F.data.startswith("quiz_answer_"),
    StateFilter(QuizStates.answering)
)
async def process_answer(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Process user's answer and send next question or finish quiz.
    """
    # Parse answer result
    is_correct = "correct" in callback.data

    # Update state
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    correct_count = data.get("correct_count", 0)
    questions_ids = data.get("questions_ids", [])

    if is_correct:
        correct_count += 1

    current_index += 1

    await state.update_data(
        current_index=current_index,
        correct_count=correct_count
    )

    # Check if quiz is finished
    if current_index >= len(questions_ids):
        # Delete the last question message before showing results
        try:
            await callback.message.delete()
        except Exception:
            pass
        await finish_quiz(callback, state, session)
    else:
        # Send next question
        await send_next_question(callback.message, state, session)

    await callback.answer()


async def finish_quiz(message_or_callback, state: FSMContext, session: AsyncSession):
    """
    Finish the quiz - calculate score, save to DB, show results and updated queue.
    """
    data = await state.get_data()
    correct_count = data.get("correct_count", 0)
    room_id = data.get("room_id")
    room_name = data.get("room_name")

    # Calculate points: 2 points per correct answer
    total_points = correct_count * 2

    # Get message object to retrieve user_id
    if isinstance(message_or_callback, types.CallbackQuery):
        user_id = message_or_callback.from_user.id
        msg = message_or_callback.message
    else:
        user_id = message_or_callback.from_user.id
        msg = message_or_callback

    student = await get_student_by_tg_id(session, user_id)

    if student and room_id:
        # Update points in database
        # Reset and set points to current quiz result
        queue_item = await get_queue_position_by_student_and_room(session, student.id, room_id)
        if queue_item:
            queue_item.points = total_points
            await session.commit()
            await session.refresh(queue_item)

    # Build results message
    results_text = (
        f"🏁 Квиз завершен!\n\n"
        f"📍 Комната: {room_name}\n"
        f"✅ Правильно: {correct_count}/{QUIZ_QUESTIONS_COUNT}\n"
        f"🏆 Ваши баллы: {total_points}\n"
    )
    # Show results
    await msg.answer(results_text)

    # Show updated queue with sorted participants
    await show_quiz_results_queue(msg, room_id, session)

    # Show actions keyboard (leave queue / back to rooms)
    try:
        keyboard = await get_queue_keyboard(user_id, room_id, session)
        if keyboard:
            await msg.answer("Выберите действие:", reply_markup=keyboard)
    except Exception:
        pass

    # Clear state
    await state.clear()


# Guard: block unrelated actions during quiz states
@quiz_router.message(StateFilter(QuizStates.answering))
async def block_messages_during_quiz(message: types.Message):
    await message.answer("Вы проходите квиз. Пожалуйста, используйте кнопки для ответов.")


@quiz_router.callback_query(StateFilter(QuizStates.answering))
async def block_other_callbacks_during_quiz(callback: types.CallbackQuery):
    # Allow only quiz answer callbacks to pass; others are blocked with a notice
    if not callback.data.startswith("quiz_answer_"):
        await callback.answer("Вы проходите квиз. Завершите его, чтобы продолжить.", show_alert=True)
        return


async def show_quiz_results_queue(message: types.Message, room_id: int, session: AsyncSession):
    """
    Show the updated queue sorted by points after quiz completion.
    """
    room = await get_object_by_id(session, Room, room_id)
    if not room:
        return

    queue_with_students = await get_queue_by_room_with_students(session, room_id)

    if not queue_with_students:
        await message.answer("Очередь пуста.")
        return

    # Build queue display text
    lines = [f"📊 Результаты квиза в '{room.name}':\n"]

    for i, queue in enumerate(queue_with_students, 1):
        lines.append(f"{i}. {queue.student.name} - {queue.points} 🏆")

    queue_text = "\n".join(lines)
    await message.answer(queue_text)
