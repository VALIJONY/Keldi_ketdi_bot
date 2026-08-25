import asyncio

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import ADMIN_IDS, TIMEZONE, POLL_HOUR, POLL_MINUTE, REPORT_HOUR, REPORT_MINUTE, REMINDER_COUNT, REMINDER_INTERVAL_MINUTES
from app.database import get_active_employees, get_unresponded_employees, tomorrow
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
    target_date = tomorrow()
    employees = await get_active_employees()
    for emp in employees:
        try:
            await bot.send_message(
                emp["user_id"],
                f"🌅 Assalomu alaykum!\n\nErtaga ({target_date}) ishga kelasizmi?",
                reply_markup=attendance_keyboard(),
            )
        except Exception:
            pass

    for i in range(1, REMINDER_COUNT + 1):
        await asyncio.sleep(REMINDER_INTERVAL_MINUTES * 60)
        unresponded = await get_unresponded_employees(target_date)
        if not unresponded:
            break
        for emp in unresponded:
            try:
                await bot.send_message(
                    emp["user_id"],
                    f"⏰ Eslatma ({i}/{REMINDER_COUNT}): Ertaga ({target_date}) ishga kelasizmi?\n"
                    "Iltimos, javob bering:",
                    reply_markup=attendance_keyboard(),
                )
            except Exception:
                pass


async def send_daily_report(bot: Bot):
    target_date = tomorrow()
    report = await build_report(target_date)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, report, parse_mode="HTML")
        except Exception:
            pass
