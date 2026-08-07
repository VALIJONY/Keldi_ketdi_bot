from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.database import record_attendance, update_attendance_reason, is_employee

router = Router()


class AttendanceState(StatesGroup):
    waiting_reason = State()


@router.callback_query(F.data == "attend_yes")
async def attend_yes(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not await is_employee(user_id):
        await callback.answer("Siz hodim emassiz.", show_alert=True)
        return

    today = date.today().isoformat()
    await record_attendance(user_id, today, "yes")
    await callback.message.edit_text("✅ Javobingiz qabul qilindi: Bugun kelasiz.")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "attend_no")
async def attend_no(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not await is_employee(user_id):
        await callback.answer("Siz hodim emassiz.", show_alert=True)
        return

    today = date.today().isoformat()
    await record_attendance(user_id, today, "no")
    await callback.message.edit_text(
        "❌ Bugun kelmaYsiz.\n\n"
        "📝 Sababni qisqacha yozing (masalan: kasalman, zarur ishim bor):"
    )
    await state.set_state(AttendanceState.waiting_reason)
    await callback.answer()


@router.message(AttendanceState.waiting_reason)
async def receive_reason(message: Message, state: FSMContext):
    reason = message.text.strip()

    if len(reason.split()) > 50:
        await message.answer("⚠️ Juda uzun. Iltimos, 50 so'z ichida yozing:")
        return

    today = date.today().isoformat()
    await update_attendance_reason(message.from_user.id, today, reason)
    await message.answer(f"✅ Sabab qabul qilindi: {reason}")
    await state.clear()
