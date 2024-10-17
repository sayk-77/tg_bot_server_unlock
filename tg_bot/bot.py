import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from tg_bot.bot_instance import bot
from tg_bot.handlers import register_handlers

load_dotenv()
TOKEN = os.getenv('TOKEN')


async def main():
    logging.basicConfig(level=logging.INFO)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    register_handlers(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
