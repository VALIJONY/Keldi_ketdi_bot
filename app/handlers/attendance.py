from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.database import record_attendance, is_employee

router = Router()


@router.callback_query(F.data == "attend_yes")
async def attend_yes(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await is_employee(user_id):
        await callback.answer("Siz hodim emassiz.", show_alert=True)
        return

    today = date.today().isoformat()
    await record_attendance(user_id, today, "yes")
    await callback.message.edit_text("✅ Javobingiz qabul qilindi: Bugun kelasiz.")
    await callback.answer()


@router.callback_query(F.data == "attend_no")
async def attend_no(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await is_employee(user_id):
        await callback.answer("Siz hodim emassiz.", show_alert=True)
        return

    today = date.today().isoformat()
    await record_attendance(user_id, today, "no")
    await callback.message.edit_text("❌ Javobingiz qabul qilindi: Bugun kelmaYsiz.")
    await callback.answer()
