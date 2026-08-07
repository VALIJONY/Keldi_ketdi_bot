from datetime import date

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import ADMIN_IDS, TIMEZONE, POLL_HOUR, POLL_MINUTE, REPORT_HOUR, REPORT_MINUTE
from app.database import get_active_employees
from app.keyboards.inline import attendance_keyboard
from app.handlers.admin import build_report


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    scheduler.add_job(
        send_daily_poll,
        CronTrigger(hour=POLL_HOUR, minute=POLL_MINUTE, timezone=TIMEZONE),
        args=[bot],
        id="daily_poll",
        replace_existing=True,
    )

    scheduler.add_job(
        send_daily_report,
        CronTrigger(hour=REPORT_HOUR, minute=REPORT_MINUTE, timezone=TIMEZONE),
        args=[bot],
        id="daily_report",
        replace_existing=True,
    )

    return scheduler


async def send_daily_poll(bot: Bot):
    employees = await get_active_employees()
    for emp in employees:
        try:
            await bot.send_message(
                emp["user_id"],
                "🌅 Assalomu alaykum!\n\nBugun ishga kelasizmi?",
                reply_markup=attendance_keyboard(),
            )
        except Exception:
            pass


async def send_daily_report(bot: Bot):
    today = date.today().isoformat()
    report = await build_report(today)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, report, parse_mode="HTML")
        except Exception:
            pass
