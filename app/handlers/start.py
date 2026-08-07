from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS
from app.database import add_employee, is_employee
from app.keyboards.inline import confirm_employee_keyboard

router = Router()

pending_users = {}


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    if user_id in ADMIN_IDS:
        if not await is_employee(user_id):
            await add_employee(user_id, full_name, username)
        await message.answer(
            "👋 Salom, Admin!\n\n"
            "Siz ham har kuni davomatga qo'shilasiz.\n\n"
            "Buyruqlar:\n"
            "/list — Hodimlar ro'yxati\n"
            "/remove — Hodimni o'chirish\n"
            "/report — Bugungi hisobot\n"
            "/help — Yordam"
        )
        return

    if await is_employee(user_id):
        await message.answer("✅ Siz allaqachon hodim sifatida ro'yxatdan o'tgansiz.")
        return

    pending_users[user_id] = {"full_name": full_name, "username": username}

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🆕 Yangi foydalanuvchi botni ishga tushirdi:\n\n"
                f"👤 Ism: {full_name}\n"
                f"🔗 Username: @{username if username else 'yo`q'}\n"
                f"🆔 ID: {user_id}\n\n"
                f"Hodim sifatida qo'shasizmi?",
                reply_markup=confirm_employee_keyboard(user_id),
            )
        except Exception:
            pass

    await message.answer(
        "👋 Salom! Sizning so'rovingiz adminga yuborildi.\n"
        "Tasdiqlangandan so'ng, har kuni ertalab sizdan so'rov keladi."
    )


@router.callback_query(F.data.startswith("add_emp_"))
async def add_employee_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Sizda ruxsat yo'q!", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    user_info = pending_users.pop(user_id, None)

    if not user_info:
        await callback.answer("Foydalanuvchi topilmadi yoki allaqachon qo'shilgan.")
        return

    await add_employee(user_id, user_info["full_name"], user_info["username"])
    await callback.message.edit_text(
        f"✅ {user_info['full_name']} hodim sifatida qo'shildi!"
    )

    try:
        await callback.bot.send_message(
            user_id,
            "🎉 Tabriklaymiz! Siz hodim sifatida tasdiqlangingiz.\n"
            "Har kuni ertalab sizdan davomat so'rovi keladi."
        )
    except Exception:
        pass

    await callback.answer()


@router.callback_query(F.data.startswith("reject_emp_"))
async def reject_employee_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Sizda ruxsat yo'q!", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    user_info = pending_users.pop(user_id, None)
    name = user_info["full_name"] if user_info else "Noma'lum"

    await callback.message.edit_text(f"❌ {name} rad etildi.")
    await callback.answer()
