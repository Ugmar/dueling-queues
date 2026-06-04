from aiogram import F, types, Router
from aiogram.filters import Command, CommandStart, StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.orm_query import is_admin

user_private_router = Router()


@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    if await is_admin(session, message.from_user.id):
        await message.answer(f"Опа... админ - @{message.from_user.username} - зашел на сервер..")
    else:
        await message.answer(f"Добро пожаловать, новый пользователь! @{message.from_user.username}\nЗарегистрируйтесь пожалуйста! -> /reg")
