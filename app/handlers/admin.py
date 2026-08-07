from datetime import date

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS
from app.database import get_employee_list, remove_employee, get_today_attendance
from app.keyboards.inline import employee_remove_keyboard

router = Router()


def admin_only(message: Message) -> bool:
    return message.from_user.id in ADMIN_IDS


@router.message(Command("list"), admin_only)
async def cmd_list(message: Message):
    employees = await get_employee_list()
    if not employees:
        await message.answer("📋 Hodimlar ro'yxati bo'sh.")
        return

    text = "📋 <b>Hodimlar ro'yxati:</b>\n\n"
    for i, emp in enumerate(employees, 1):
        username = f"@{emp['username']}" if emp["username"] else "username yo'q"
        text += f"{i}. {emp['full_name']} ({username})\n"

    text += f"\n<b>Jami: {len(employees)} hodim</b>"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("remove"), admin_only)
async def cmd_remove(message: Message):
    employees = await get_employee_list()
    if not employees:
        await message.answer("📋 Hodimlar ro'yxati bo'sh.")
        return

    text = "🗑 O'chirish uchun hodimni tanlang:\n\n"
    for emp in employees:
        username = f"@{emp['username']}" if emp["username"] else ""
        text += f"• {emp['full_name']} {username}\n"
        await message.answer(
            f"👤 {emp['full_name']} {username}",
            reply_markup=employee_remove_keyboard(emp["user_id"]),
        )


@router.callback_query(F.data.startswith("remove_emp_"))
async def remove_employee_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Sizda ruxsat yo'q!", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    await remove_employee(user_id)
    await callback.message.edit_text("✅ Hodim muvaffaqiyatli o'chirildi.")
    await callback.answer()


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery):
    await callback.message.edit_text("⬅️ Bekor qilindi.")
    await callback.answer()


@router.message(Command("report"), admin_only)
async def cmd_report(message: Message):
    today = date.today().isoformat()
    report = await build_report(today)
    await message.answer(report, parse_mode="HTML")


@router.message(Command("help"), admin_only)
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Admin buyruqlari:</b>\n\n"
        "/list — Hodimlar ro'yxati\n"
        "/remove — Hodimni o'chirish\n"
        "/report — Bugungi davomat hisoboti\n"
        "/help — Ushbu yordam",
        parse_mode="HTML",
    )


async def build_report(today: str) -> str:
    records = await get_today_attendance(today)

    coming = []
    not_coming = []
    no_response = []

    for r in records:
        name = r["full_name"]
        if r["response"] == "yes":
            coming.append(name)
        elif r["response"] == "no":
            not_coming.append(name)
        else:
            no_response.append(name)

    text = f"📊 <b>Davomat hisoboti — {today}</b>\n\n"

    text += f"✅ <b>Keladi ({len(coming)}):</b>\n"
    for name in coming:
        text += f"  • {name}\n"
    if not coming:
        text += "  — hech kim\n"

    text += f"\n❌ <b>Kelmaydi ({len(not_coming)}):</b>\n"
    for name in not_coming:
        text += f"  • {name}\n"
    if not not_coming:
        text += "  — hech kim\n"

    if no_response:
        text += f"\n⚠️ <b>Javob bermagan ({len(no_response)}):</b>\n"
        for name in no_response:
            text += f"  • {name}\n"

    text += f"\n<b>Jami: {len(coming)} keladi, {len(not_coming)} kelmaydi"
    if no_response:
        text += f", {len(no_response)} javob bermagan"
    text += "</b>"

    return text
