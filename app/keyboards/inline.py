from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def attendance_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, kelaman", callback_data="attend_yes"),
            InlineKeyboardButton(text="❌ Yo'q, kelmayman", callback_data="attend_no"),
        ]
    ])


def confirm_employee_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qo'shish", callback_data=f"add_emp_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_emp_{user_id}"),
        ]
    ])


def employee_remove_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"remove_emp_{user_id}"),
            InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="cancel_action"),
        ]
    ])
