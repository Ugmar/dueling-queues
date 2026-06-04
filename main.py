from app.database.engine import AsyncSessionLocal
from app.middlewares.db import DataBaseSession
from app.middlewares.quiz_guard import QuizGuard
from app.handlers.user_private import user_private_router
from app.fsm.reg import reg_router
from app.fsm.add import add_material_router
from app.fsm.queue import queue_router
from app.fsm.quiz import quiz_router
import os
from dotenv import load_dotenv

import asyncio
from aiogram import Bot, Dispatcher, types
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()


bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

dp.update.middleware(DataBaseSession(session_pool=AsyncSessionLocal))
dp.update.middleware(QuizGuard())
dp.include_router(reg_router)
dp.include_router(queue_router)
dp.include_router(quiz_router)
dp.include_router(add_material_router)
# dp.include_router(admin_private_router)
dp.include_router(user_private_router)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Бот запущен...')
    asyncio.run(main())
