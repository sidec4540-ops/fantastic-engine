from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart
from aiogram.enums.chat_member_status import ChatMemberStatus

import database as db
from keyboards.inline import create_pagination_keyboard

router = Router()
user_search_results = {}

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "🎁 <b>Приветствую!</b>\n\n"
        "Я бот для автоматического поиска NFT-подарков.\n\n"
        "<b>Доступные команды:</b>\n"
        "/search - Начать поиск подарков\n"
        "/random - 30 рандомных юзеров (в разработке)\n\n"
        "❤️ Сделано с любовью от mvpcrazy\n"
        "🧑‍💻 Форум - https://lolz.live/members/3478629/"
    )
    await message.answer(text, disable_web_page_preview=True)

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(query: types.CallbackQuery, bot: Bot):
    channel_username = await db.get_subscription_channel()
    if not channel_username:
        await query.answer("Проверка отключена администратором.", show_alert=True)
        return

    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=query.from_user.id)
        if member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        ]:
            await query.answer("Спасибо за подписку!", show_alert=True)
            await query.message.delete()
        else:
            await query.answer("Вы все еще не подписаны.", show_alert=True)
    except Exception:
        await query.answer("Не удалось проверить подписку. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data.startswith("result_page_"))
async def result_pagination_handler(query: types.CallbackQuery):
    chat_id = query.message.chat.id
    if chat_id not in user_search_results:
        await query.answer("Результаты поиска устарели.", show_alert=True)
        return

    page = int(query.data.split("_")[2])
    pages = user_search_results[chat_id]

    if 0 <= page < len(pages):
        keyboard = create_pagination_keyboard(current_page=page, total_pages=len(pages), prefix="result_page")
        await query.message.edit_text(pages[page], reply_markup=keyboard, disable_web_page_preview=True)

    await query.answer()

@router.callback_query(F.data == "noop")
async def noop_callback(query: types.CallbackQuery):
    await query.answer()