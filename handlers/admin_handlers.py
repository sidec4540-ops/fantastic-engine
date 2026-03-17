import asyncio
import aiohttp
from aiogram import Router, types
from aiogram.filters import Command

from filters.admin import IsAdminFilter
import database as db
from services.proxy_manager import proxy_manager

router = Router()
router.message.filter(IsAdminFilter())


async def check_proxy(session: aiohttp.ClientSession, proxy_str: str) -> bool:
    proxy_url = None
    try:
        if "://" in proxy_str:
            proxy_url = proxy_str
        else:
            ip, port, login, password = proxy_str.split(":")
            proxy_url = f"socks5://{login}:{password}@{ip}:{port}"

        async with session.get("https://api.ipify.org?format=json", proxy=proxy_url, timeout=10) as response:
            return response.status == 200 and await response.json()
    except Exception:
        return False


@router.message(Command("admin"))
async def cmd_admin_panel(message: types.Message):
    text = (
        "<b>Админ-панель</b>\n\n"
        "<b>Управление доступом:</b>\n"
        "<code>/block ID</code> - заблокировать пользователя\n"
        "<code>/unblock ID</code> - разблокировать\n"
        "<code>/blacklist @user</code> - добавить юзернейм в ЧС поиска\n"
        "<code>/unblacklist @user</code> - убрать юзернейм из ЧС\n\n"
        "<b>Управление каналом:</b>\n"
        "<code>/setchannel @username</code> - установить канал для подписки\n"
        "<code>/delchannel</code> - отключить проверку подписки\n"
        "<code>/channelstatus</code> - текущий статус проверки\n\n"
        "<b>Управление прокси:</b>\n"
        "<code>/addproxy proxy</code> - добавить прокси\n"
        "<code>/delproxy proxy</code> - удалить прокси\n"
        "<code>/listproxies</code> - показать все прокси\n"
        "<code>/checkproxies</code> - проверить прокси на работоспособность"
    )
    await message.answer(text)


@router.message(Command("checkproxies"))
async def cmd_check_proxies(message: types.Message):
    proxies = await db.get_all_proxies()
    if not proxies:
        await message.answer("Список прокси пуст. Нечего проверять.")
        return

    status_message = await message.answer(
        f"Начинаю проверку {len(proxies)} прокси... Это может занять некоторое время.")

    working_proxies = []
    failed_proxies = []

    async with aiohttp.ClientSession() as session:
        tasks = [check_proxy(session, p) for p in proxies]
        results = await asyncio.gather(*tasks)

    for proxy, is_working in zip(proxies, results):
        if is_working:
            working_proxies.append(proxy)
        else:
            failed_proxies.append(proxy)

    text = f"✅ <b>Проверка завершена!</b>\n\n"
    text += f"🟢 <b>Работают ({len(working_proxies)}):</b>\n"
    text += "\n".join([f"<code>{p.replace('<', '&lt;').replace('>', '&gt;')}</code>" for p in
                       working_proxies]) or "Нет рабочих прокси."
    text += f"\n\n🔴 <b>Не работают ({len(failed_proxies)}):</b>\n"
    text += "\n".join([f"<code>{p.replace('<', '&lt;').replace('>', '&gt;')}</code>" for p in
                       failed_proxies]) or "Все прокси в списке работают."

    await status_message.edit_text(text)


@router.message(Command("block"))
async def cmd_block_user(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        await db.block_user(user_id)
        await message.answer(f"✅ Пользователь с ID <code>{user_id}</code> заблокирован.")
    except (IndexError, ValueError):
        await message.answer("❗️Неверный формат. Используй: /block ID")


@router.message(Command("unblock"))
async def cmd_unblock_user(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        await db.unblock_user(user_id)
        await message.answer(f"✅ Пользователь с ID <code>{user_id}</code> разблокирован.")
    except (IndexError, ValueError):
        await message.answer("❗️Неверный формат. Используй: /unblock ID")


@router.message(Command("blacklist"))
async def cmd_blacklist_user(message: types.Message):
    try:
        username = message.text.split()[1]
        if not username.startswith("@"): raise ValueError()
        await db.add_to_blacklist(username)
        await message.answer(f"✅ Пользователь <code>{username}</code> добавлен в черный список поиска.")
    except (IndexError, ValueError):
        await message.answer("❗️Неверный формат. Используй: /blacklist @username")


@router.message(Command("unblacklist"))
async def cmd_unblacklist_user(message: types.Message):
    try:
        username = message.text.split()[1]
        if not username.startswith("@"): raise ValueError()
        await db.remove_from_blacklist(username)
        await message.answer(f"✅ Пользователь <code>{username}</code> удален из черного списка поиска.")
    except (IndexError, ValueError):
        await message.answer("❗️Неверный формат. Используй: /unblacklist @username")


@router.message(Command("setchannel"))
async def cmd_set_channel(message: types.Message):
    args = message.text.split()
    if len(args) != 2 or not args[1].startswith("@"):
        await message.answer("❗️Использование: /setchannel @username")
        return

    channel = args[1]
    await db.set_subscription_channel(channel)
    await message.answer(f"✅ Проверка подписки установлена на канал: {channel}")


@router.message(Command("delchannel"))
async def cmd_del_channel(message: types.Message):
    await db.set_subscription_channel(None)
    await message.answer("✅ Проверка подписки отключена.")


@router.message(Command("channelstatus"))
async def cmd_channel_status(message: types.Message):
    channel = await db.get_subscription_channel()
    if channel:
        await message.answer(f"ℹ️ Проверка включена для канала: {channel}")
    else:
        await message.answer("ℹ️ Проверка сейчас отключена.")


@router.message(Command("addproxy"))
async def cmd_add_proxy(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❗️Использование: /addproxy proxy_string")
        return

    proxy_str = args[1]
    if await db.add_proxy(proxy_str):
        await proxy_manager.load_proxies()
        await message.answer(f"✅ Прокси `{proxy_str}` успешно добавлен.")
    else:
        await message.answer(f"❌ Не удалось добавить прокси `{proxy_str}`. Возможно, он уже существует.")


@router.message(Command("delproxy"))
async def cmd_del_proxy(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❗️Использование: /delproxy proxy_string")
        return

    proxy_str = args[1]
    if await db.delete_proxy(proxy_str):
        await proxy_manager.load_proxies()
        await message.answer(f"✅ Прокси `{proxy_str}` удален.")
    else:
        await message.answer(f"❌ Прокси `{proxy_str}` не найден в базе.")


@router.message(Command("listproxies"))
async def cmd_list_proxies(message: types.Message):
    proxies = await db.get_all_proxies()
    if not proxies:
        await message.answer("Список прокси пуст.")
        return

    text = "<b>Список добавленных прокси:</b>\n\n"
    text += "\n".join([f"<code>{p.replace('<', '&lt;').replace('>', '&gt;')}</code>" for p in proxies])
    await message.answer(text)