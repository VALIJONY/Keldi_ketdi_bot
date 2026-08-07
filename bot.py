import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from app.database import init_db
from app.handlers import start_router, admin_router, attendance_router
from app.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(attendance_router)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    logging.info("Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
