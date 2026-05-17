import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.models import Database
from handlers import registration, search, contacts


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot_token = os.getenv("BOT_TOKEN")
    db_path = os.getenv("DATABASE_PATH", "finguide.db")

    if not bot_token:
        logger.error("BOT_TOKEN not found in .env file")
        return

    # Инициализация бота и диспетчера
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Инициализация базы данных
    db = Database(db_path)
    await db.connect()

    # Регистрация роутеров
    dp.include_router(registration.router)
    dp.include_router(search.router)
    dp.include_router(contacts.router)

    # Передача БД в middleware
    @dp.message.middleware()
    @dp.callback_query.middleware()
    async def db_middleware(handler, event, data):
        data["db"] = db
        return await handler(event, data)

    logger.info("Bot started")

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
