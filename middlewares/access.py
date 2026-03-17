from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.enums.chat_member_status import ChatMemberStatus

import config
import database as db
from keyboards.inline import get_subscription_keyboard


class AccessMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id

        if user_id == config.OWNER_ID:
            return await handler(event, data)

        if await db.is_user_blocked(user_id):
            return

        channel_username = await db.get_subscription_channel()

        if not channel_username:
            return await handler(event, data)

        bot: Bot = data['bot']

        try:
            member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status in [
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR
            ]:
                return await handler(event, data)
        except Exception:
            pass

        text = f"Для использования бота необходимо подписаться на канал: {channel_username}"
        keyboard = get_subscription_keyboard(channel_username)

        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        elif isinstance(event, CallbackQuery):
            await event.answer("Сначала подпишитесь на канал.", show_alert=True)
            await event.message.answer(text, reply_markup=keyboard)