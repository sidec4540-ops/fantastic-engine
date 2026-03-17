from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_pagination_keyboard(current_page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []

    if current_page > 0:
        row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}_{current_page - 1}"))

    row.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="noop"))

    if current_page < total_pages - 1:
        row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"{prefix}_{current_page + 1}"))

    buttons.append(row)
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_subscription_keyboard(channel_username: str) -> InlineKeyboardMarkup:
    if channel_username.startswith('@'):
        channel_username = channel_username[1:]

    buttons = [
        [InlineKeyboardButton(text="✅ Подписаться", url=f"https://t.me/{channel_username}")],
        [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_subscription")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard