from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.database import (
    record_attendance, update_attendance_reason, is_employee, tomorrow,
    record_poll_response, update_poll_reason,
)

router = Router()


class AttendanceState(StatesGroup):
    waiting_reason = State()


# --- Daily attendance (ertaga uchun) ---

@router.callback_query(F.data == "attend_yes")
async def attend_yes(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not await is_employee(user_id):
        await callback.answer("Siz hodim emassiz.", show_alert=True)
        return

    target_date = tomorrow()
    await record_attendance(user_id, target_date, "yes")
    await callback.message.edit_text(f"✅ Javobingiz qabul qilindi: Ertaga ({target_date}) kelasiz.")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "attend_no")
async def attend_no(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not await is_employee(user_id):
        await callback.answer("Siz hodim emassiz.", show_alert=True)
        return

    target_date = tomorrow()
    await record_attendance(user_id, target_date, "no")
    await state.update_data(reason_type="daily", target_date=target_date)
    await callback.message.edit_text(
        f"❌ Ertaga ({target_date}) kelmaYsiz.\n\n"
        "📝 Sababni qisqacha yozing (masalan: kasalman, zarur ishim bor):"
    )
    await state.set_state(AttendanceState.waiting_reason)
    await callback.answer()


# --- Poll session callbacks ---

@router.callback_query(F.data.startswith("poll_yes:"))
async def poll_yes(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not await is_employee(user_id):
        await callback.answer("Siz hodim emassiz.", show_alert=True)
        return

    session_id = callback.data.split(":")[1]
    await record_poll_response(session_id, user_id, "yes")
    await callback.message.edit_text("✅ Javobingiz qabul qilindi.")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("poll_no:"))
async def poll_no(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if not await is_employee(user_id):
        await callback.answer("Siz hodim emassiz.", show_alert=True)
        return

    session_id = callback.data.split(":")[1]
    await record_poll_response(session_id, user_id, "no")
    await state.update_data(reason_type="poll", session_id=session_id)
    await callback.message.edit_text(
        "❌ Kelmaysiz.\n\n"
        "📝 Sababni qisqacha yozing (masalan: kasalman, zarur ishim bor):"
    )
    await state.set_state(AttendanceState.waiting_reason)
    await callback.answer()


# --- Reason handler (both daily and poll) ---

@router.message(AttendanceState.waiting_reason)
async def receive_reason(message: Message, state: FSMContext):
    reason = message.text.strip()

    if len(reason.split()) > 50:
        await message.answer("⚠️ Juda uzun. Iltimos, 50 so'z ichida yozing:")
        return

    data = await state.get_data()
    reason_type = data.get("reason_type", "daily")

    if reason_type == "poll":
        session_id = data["session_id"]
        await update_poll_reason(session_id, message.from_user.id, reason)
    else:
        target_date = data.get("target_date", tomorrow())
        await update_attendance_reason(message.from_user.id, target_date, reason)

    await message.answer(f"✅ Sabab qabul qilindi: {reason}")
    await state.clear()
