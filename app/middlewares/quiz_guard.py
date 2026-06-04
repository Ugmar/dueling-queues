from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from app.fsm.quiz.states import QuizStates


class QuizGuard(BaseMiddleware):
    """Middleware to restrict user actions while passing a quiz.

    Allows only quiz answer callbacks during QuizStates.answering.
    Blocks other messages/callbacks with a friendly notice.
    """

    async def __call__(self, handler, event, data):
        state: FSMContext | None = data.get("state")
        if state is not None:
            current = await state.get_state()
            if current == QuizStates.answering.state:
                # Allow only quiz answer callbacks to pass through
                if isinstance(event, types.CallbackQuery):
                    if event.data and event.data.startswith("quiz_answer_"):
                        return await handler(event, data)
                    await event.answer("Вы проходите квиз. Завершите его, чтобы продолжить.", show_alert=True)
                    return
                if isinstance(event, types.Message):
                    await event.answer("Вы проходите квиз. Пожалуйста, используйте кнопки для ответов.")
                    return

        return await handler(event, data)
