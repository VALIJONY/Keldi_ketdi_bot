from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def attendance_keyboard(session_id: str | None = None, yes_text: str = "✅ Ha, kelaman", no_text: str = "❌ Yo'q, kelmayman") -> InlineKeyboardMarkup:
    if session_id:
        yes_data = f"poll_yes:{session_id}"
        no_data = f"poll_no:{session_id}"
    else:
        yes_data = "attend_yes"
        no_data = "attend_no"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=yes_text, callback_data=yes_data),
            InlineKeyboardButton(text=no_text, callback_data=no_data),
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
