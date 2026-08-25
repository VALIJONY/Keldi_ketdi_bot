import asyncio

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS, MANUAL_POLL_WAIT_MINUTES
from app.database import (
    get_employee_list, get_active_employees, remove_employee,
    get_today_attendance, tomorrow,
    create_poll_session, get_poll_results,
)
from app.keyboards.inline import employee_remove_keyboard, attendance_keyboard

router = Router()


class CustomPollState(StatesGroup):
    waiting_text = State()
    waiting_buttons = State()


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

    for emp in employees:
        username = f"@{emp['username']}" if emp["username"] else ""
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
    target_date = tomorrow()
    report = await build_report(target_date)
    await message.answer(report, parse_mode="HTML")


@router.message(Command("poll"), admin_only)
async def cmd_poll(message: Message):
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        wait = int(args[1])
    else:
        wait = MANUAL_POLL_WAIT_MINUTES

    session_id = await create_poll_session(message.from_user.id, wait)
    employees = await get_active_employees()

    count = 0
    for emp in employees:
        try:
            await message.bot.send_message(
                emp["user_id"],
                f"🌅 Assalomu alaykum!\n\nErtaga ({tomorrow()}) ishga kelasizmi?",
                reply_markup=attendance_keyboard(session_id=session_id),
            )
            count += 1
        except Exception:
            pass

    await message.answer(
        f"✅ So'rov {count} ta hodimga yuborildi.\n"
        f"⏱ Hisobot {wait} daqiqadan so'ng avtomatik keladi."
    )

    await asyncio.sleep(wait * 60)

    report = await build_poll_report(session_id)
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, report, parse_mode="HTML")
        except Exception:
            pass


@router.message(Command("custom"), admin_only)
async def cmd_custom(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    wait = MANUAL_POLL_WAIT_MINUTES

    if len(args) > 1 and args[1].strip():
        first_word = args[1].split()[0]
        if first_word.isdigit():
            wait = int(first_word)

    await state.update_data(custom_wait=wait)
    await message.answer(
        "📝 <b>1-qadam:</b> Xabar matnini yozing.\n\n"
        "Bu matn hodimga tugmalar bilan yuboriladi.\n\n"
        "Masalan: <i>Ertaga ishga kelasizmi? Muhim yig'ilish bor.</i>",
        parse_mode="HTML",
    )
    await state.set_state(CustomPollState.waiting_text)


@router.message(CustomPollState.waiting_text, admin_only)
async def custom_poll_text(message: Message, state: FSMContext):
    custom_text = message.text.strip()
    await state.update_data(custom_text=custom_text)
    await message.answer(
        "📝 <b>2-qadam:</b> Tugma textlarini yozing.\n\n"
        "Format: <code>Ha matni | Yo'q matni</code>\n\n"
        "Masalan: <code>Kelaman ✅ | Kelmayman ❌</code>\n\n"
        "Standart tugmalar uchun <code>-</code> yozing.",
        parse_mode="HTML",
    )
    await state.set_state(CustomPollState.waiting_buttons)


@router.message(CustomPollState.waiting_buttons, admin_only)
async def custom_poll_buttons(message: Message, state: FSMContext):
    data = await state.get_data()
    custom_text = data["custom_text"]
    wait = data.get("custom_wait", MANUAL_POLL_WAIT_MINUTES)

    btn_input = message.text.strip()
    if btn_input == "-":
        yes_text = "✅ Ha, kelaman"
        no_text = "❌ Yo'q, kelmayman"
    elif "|" in btn_input:
        parts = btn_input.split("|", 1)
        yes_text = parts[0].strip() or "✅ Ha, kelaman"
        no_text = parts[1].strip() or "❌ Yo'q, kelmayman"
    else:
        await message.answer("⚠️ Noto'g'ri format. <code>Ha matni | Yo'q matni</code> yoki <code>-</code> yozing.", parse_mode="HTML")
        return

    await state.clear()

    session_id = await create_poll_session(message.from_user.id, wait)
    employees = await get_active_employees()

    count = 0
    for emp in employees:
        try:
            await message.bot.send_message(
                emp["user_id"],
                custom_text,
                reply_markup=attendance_keyboard(session_id=session_id, yes_text=yes_text, no_text=no_text),
            )
            count += 1
        except Exception:
            pass

    await message.answer(
        f"✅ Maxsus so'rov {count} ta hodimga yuborildi.\n"
        f"⏱ Hisobot {wait} daqiqadan so'ng avtomatik keladi."
    )

    await asyncio.sleep(wait * 60)

    report = await build_poll_report(session_id)
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, report, parse_mode="HTML")
        except Exception:
            pass


@router.message(Command("help"), admin_only)
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Admin buyruqlari:</b>\n\n"
        "/list — Hodimlar ro'yxati\n"
        "/remove — Hodimni o'chirish\n"
        "/report — Ertangi davomat hisoboti\n"
        f"/poll — Hammaga so'rov yuborish ({MANUAL_POLL_WAIT_MINUTES} daq kutadi)\n"
        "/poll 10 — So'rov yuborish (10 daq kutadi)\n"
        "/custom — Maxsus matnli + tugmali so'rov\n"
        "/custom 10 — Maxsus so'rov (10 daq kutadi)\n"
        "/help — Ushbu yordam",
        parse_mode="HTML",
    )


async def build_report(target_date: str) -> str:
    records = await get_today_attendance(target_date)

    coming = []
    not_coming = []
    no_response = []

    for r in records:
        name = r["full_name"]
        reason = r["reason"]
        if r["response"] == "yes":
            coming.append(name)
        elif r["response"] == "no":
            not_coming.append({"name": name, "reason": reason})
        else:
            no_response.append(name)

    text = f"📊 <b>Davomat hisoboti — {target_date}</b>\n\n"

    text += f"✅ <b>Keladi ({len(coming)}):</b>\n"
    for name in coming:
        text += f"  • {name}\n"
    if not coming:
        text += "  — hech kim\n"

    text += f"\n❌ <b>Kelmaydi ({len(not_coming)}):</b>\n"
    for item in not_coming:
        reason_text = f" — <i>{item['reason']}</i>" if item["reason"] else ""
        text += f"  • {item['name']}{reason_text}\n"
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


async def build_poll_report(session_id: str) -> str:
    records = await get_poll_results(session_id)

    coming = []
    not_coming = []
    no_response = []

    for r in records:
        name = r["full_name"]
        reason = r["reason"]
        if r["response"] == "yes":
            coming.append(name)
        elif r["response"] == "no":
            not_coming.append({"name": name, "reason": reason})
        else:
            no_response.append(name)

    text = f"📊 <b>So'rov hisoboti (session: {session_id})</b>\n\n"

    text += f"✅ <b>Ha ({len(coming)}):</b>\n"
    for name in coming:
        text += f"  • {name}\n"
    if not coming:
        text += "  — hech kim\n"

    text += f"\n❌ <b>Yo'q ({len(not_coming)}):</b>\n"
    for item in not_coming:
        reason_text = f" — <i>{item['reason']}</i>" if item["reason"] else ""
        text += f"  • {item['name']}{reason_text}\n"
    if not not_coming:
        text += "  — hech kim\n"

    if no_response:
        text += f"\n⚠️ <b>Javob bermagan ({len(no_response)}):</b>\n"
        for name in no_response:
            text += f"  • {name}\n"

    text += f"\n<b>Jami: {len(coming)} ha, {len(not_coming)} yo'q"
    if no_response:
        text += f", {len(no_response)} javob bermagan"
    text += "</b>"

    return text
