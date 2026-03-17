import asyncio
import html
import logging
from typing import List, Tuple

import aiohttp
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bs4 import BeautifulSoup

import database as db
from services.proxy_manager import proxy_manager
from keyboards.inline import create_pagination_keyboard
from handlers.user_handlers import user_search_results

GIFTS = {
    1: "Signet Ring", 2: "Skull Flower", 3: "Snow Mittens", 4: "Spiced Wine", 5: "Spy Agaric",
    6: "Star Notepad", 7: "Swiss Watch", 8: "Trapped Heart", 9: "Vintage Cigar", 10: "Voodoo Doll",
    11: "Witch Hat", 12: "Lunar Snake", 13: "Mad Pumpkin", 14: "Magic Potion", 15: "Mini Oscar",
    16: "Party Sparkler", 17: "Perfume Bottle", 18: "Plush Pepe", 19: "Precious Peach", 20: "Santa Hat",
    21: "Scared Cat", 22: "Sharp Tongue", 23: "Hex Pot", 24: "Homemade Cake", 25: "Hypno Lollipop",
    26: "Ion Gem", 27: "Jelly Bunny", 28: "Jester Hat", 29: "Jingle Bells", 30: "Kissed Frog",
    31: "Lol Pop", 32: "Love Candle", 33: "Cookie Heart", 34: "Crystal Ball", 35: "MOOO",
    36: "Desk Calendar", 37: "Durovs Cap", 38: "Eternal Candle", 39: "Eternal Rose", 40: "Evil Eye",
    41: "Flying Broom", 42: "Genie Lamp", 43: "Ginger Cookie", 44: "Sleigh Bell", 45: "Sakura Flower",
    46: "Top Hat", 47: "Diamond Ring", 48: "Love Potion", 49: "Toy Bear", 50: "Loot Bag",
    51: "Astral Shard", 52: "HAPPY", 53: "BdAy", 54: "BDay Candle", 55: "Berry Box",
    56: "Bunny Muffin", 57: "Tama GadGet", 58: "Candy Cane", 59: "Snow Globe", 60: "Electric Skull",
    61: "Winter Wreath", 62: "Neko Helmet", 63: "Record Player", 64: "Jack In The Box", 65: "Easter Egg",
    66: "Holiday Drink", 67: "Xmas Stocking", 68: "Snake Box", 69: "Pet Snake", 70: "Big Year",
    71: "Heart Locket", 72: "Bow Tie", 73: "Heroic Helmet", 74: "Nail Bracelet", 75: "Restless Jar",
    76: "Light Sword", 77: "Gem Signet", 78: "Bonded Ring"
}

router = Router()


class SearchStates(StatesGroup):
    waiting_for_gift = State()
    waiting_for_range = State()
    waiting_for_models = State()
    waiting_for_backgrounds = State()
    waiting_for_patterns = State()


async def parse_gift_data(session: aiohttp.ClientSession, url: str) -> Tuple[str, str, str] | None:
    proxy = await proxy_manager.get_proxy()
    proxy_url = None
    if proxy:
        try:
            if "://" in proxy:
                proxy_url = proxy
            else:
                ip, port, login, password = proxy.split(":")
                proxy_url = f"socks5://{login}:{password}@{ip}:{port}"
        except Exception:
            logging.error(f"Неверный формат прокси: {proxy}")
            proxy = None

    try:
        async with session.get(url, proxy=proxy_url, timeout=15, allow_redirects=False) as response:
            if response.status == 200:
                html_text = await response.text()
                soup = BeautifulSoup(html_text, "lxml")
                owner_tag = soup.select_one('table.tgme_gift_table th:-soup-contains("Owner") + td a')
                if owner_tag and owner_tag.get('href'):
                    owner_username = "@" + owner_tag['href'].replace('https://t.me/', '')
                    return (url, owner_username, html_text)
            return None
    except Exception as e:
        if proxy:
            proxy_manager.report_failure(proxy)
        logging.debug(f"Ошибка при парсинге {url}: {e}")
        return None


@router.message(Command("search"))
async def cmd_search(message: types.Message, state: FSMContext):
    await state.clear()
    page_size = 10
    gift_items = list(GIFTS.items())
    pages = ["\n".join([f"<code>{num}</code> - {name}" for num, name in gift_items[i:i + page_size]]) for i in
             range(0, len(gift_items), page_size)]
    await state.update_data(gift_pages=pages)
    text = "<b>Шаг 1/5: Выбор подарка</b>\n\nВыберите подарок из списка или введите его номер/название."
    keyboard = create_pagination_keyboard(current_page=0, total_pages=len(pages), prefix="gift_page")
    await message.answer(f"{text}\n\n{pages[0]}", reply_markup=keyboard)
    await state.set_state(SearchStates.waiting_for_gift)


@router.callback_query(F.data.startswith("gift_page_"), SearchStates.waiting_for_gift)
async def gift_pagination_handler(query: types.CallbackQuery, state: FSMContext):
    page = int(query.data.split("_")[2])
    user_data = await state.get_data()
    pages = user_data.get("gift_pages", [])
    if 0 <= page < len(pages):
        keyboard = create_pagination_keyboard(current_page=page, total_pages=len(pages), prefix="gift_page")
        text = "<b>Шаг 1/5: Выбор подарка</b>\n\nВыберите подарок из списка или введите его номер/название."
        await query.message.edit_text(f"{text}\n\n{pages[page]}", reply_markup=keyboard)
    await query.answer()


@router.message(SearchStates.waiting_for_gift)
async def process_gift_selection(message: types.Message, state: FSMContext):
    selection = message.text.strip()
    gift_name = ""
    if selection.isdigit() and int(selection) in GIFTS:
        gift_name = GIFTS[int(selection)]
    else:
        gift_name = next((name for name in GIFTS.values() if selection.lower() == name.lower()), "")

    if not gift_name:
        await message.answer("❌ Подарок не найден. Введите его номер или точное название.")
        return

    await state.update_data(gift_name=gift_name)
    await message.answer(
        f"✅ Ищем <b>{gift_name}</b>.\n\n<b>Шаг 2/5: Диапазон поиска</b>\n\nВведи диапазон в формате <code>1-10000</code>. Максимум 20,000.")
    await state.set_state(SearchStates.waiting_for_range)


@router.message(SearchStates.waiting_for_range)
async def process_range(message: types.Message, state: FSMContext):
    try:
        start_id_str, end_id_str = message.text.strip().split('-')
        start_id, end_id = int(start_id_str), int(end_id_str)
        if not (0 < start_id <= end_id and (end_id - start_id) <= 20000):
            raise ValueError()
    except (ValueError, IndexError):
        await message.answer("❗️Неверный формат или диапазон. Введи как <code>1-10000</code>.")
        return

    await state.update_data(start_id=start_id, end_id=end_id)
    await message.answer(
        "<b>Шаг 3/5: Модели</b>\n\nВведи модели через запятую (например, <code>Common, Rare</code>) или /skip, чтобы пропустить.")
    await state.set_state(SearchStates.waiting_for_models)


@router.message(SearchStates.waiting_for_models, Command("skip"))
async def process_skip_models(message: types.Message, state: FSMContext):
    await state.update_data(models=[])
    await message.answer("<b>Шаг 4/5: Цвета фона</b>\n\nВведи цвета через запятую (<code>Red, Blue</code>) или /skip.")
    await state.set_state(SearchStates.waiting_for_backgrounds)


@router.message(SearchStates.waiting_for_models)
async def process_models(message: types.Message, state: FSMContext):
    models = [m.strip() for m in message.text.split(',') if m.strip()]
    await state.update_data(models=models)
    await message.answer("<b>Шаг 4/5: Цвета фона</b>\n\nВведи цвета через запятую (<code>Red, Blue</code>) или /skip.")
    await state.set_state(SearchStates.waiting_for_backgrounds)


@router.message(SearchStates.waiting_for_backgrounds, Command("skip"))
async def process_skip_backgrounds(message: types.Message, state: FSMContext):
    await state.update_data(backgrounds=[])
    await message.answer("<b>Шаг 5/5: Узоры</b>\n\nВведи узоры через запятую (<code>Stripes</code>) или /skip.")
    await state.set_state(SearchStates.waiting_for_patterns)


@router.message(SearchStates.waiting_for_backgrounds)
async def process_backgrounds(message: types.Message, state: FSMContext):
    backgrounds = [b.strip() for b in message.text.split(',') if b.strip()]
    await state.update_data(backgrounds=backgrounds)
    await message.answer("<b>Шаг 5/5: Узоры</b>\n\nВведи узоры через запятую (<code>Stripes</code>) или /skip.")
    await state.set_state(SearchStates.waiting_for_patterns)


@router.message(SearchStates.waiting_for_patterns, Command("skip"))
async def process_skip_patterns_and_start(message: types.Message, state: FSMContext):
    await state.update_data(patterns=[])
    await start_search_with_filters(message, state)


@router.message(SearchStates.waiting_for_patterns)
async def process_patterns_and_start(message: types.Message, state: FSMContext):
    patterns = [p.strip() for p in message.text.split(',') if p.strip()]
    await state.update_data(patterns=patterns)
    await start_search_with_filters(message, state)


async def start_search_with_filters(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    gift_name = user_data['gift_name']
    start_id = user_data['start_id']
    end_id = user_data['end_id']
    models = user_data['models']
    backgrounds = user_data['backgrounds']
    patterns = user_data['patterns']
    await state.clear()

    blacklist = await db.get_blacklist()
    status_message = await message.answer(
        f"🚀 Начинаю поиск <b>{gift_name}</b> в диапазоне <code>{start_id}-{end_id}</code>...")

    found_results: List[Tuple[str, str]] = []
    total_count = end_id - start_id + 1
    processed_count = 0

    tasks = []
    gift_slug = gift_name.replace(" ", "")

    async with aiohttp.ClientSession() as session:
        for num in range(start_id, end_id + 1):
            url = f"https://t.me/nft/{gift_slug}-{num}"
            tasks.append(asyncio.create_task(parse_gift_data(session, url)))

        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            processed_count += 1
            if result:
                url, owner, html_text = result
                html_lower = html_text.lower()

                if owner.lower() in blacklist:
                    continue
                if models and not any(m.lower() in html_lower for m in models):
                    continue
                if backgrounds and not any(b.lower() in html_lower for b in backgrounds):
                    continue
                if patterns and not any(p.lower() in html_lower for p in patterns):
                    continue

                found_results.append((url, owner))

            if i % 50 == 0 or processed_count == total_count:
                try:
                    await status_message.edit_text(
                        f"⏳ Идет поиск <b>{gift_name}</b>...\n\n"
                        f"Проверено: {processed_count}/{total_count}\n"
                        f"Найдено (с учетом фильтров): {len(found_results)}"
                    )
                except Exception:
                    pass

    await status_message.delete()

    if not found_results:
        await message.answer(f"😔 Поиск завершен. С учетом фильтров ничего не найдено.")
        return

    unique_results = list(dict.fromkeys(found_results))

    page_size = 5
    result_pages = []
    header_template = (
        f"✅ <b>Поиск завершен!</b>\n"
        f"🎁 Подарок: <b>{gift_name}</b>\n"
        f"🔢 Диапазон: {start_id}-{end_id}\n"
        f"👥 Найдено с учетом фильтров: {len(unique_results)}\n\n"
    )

    for i in range(0, len(unique_results), page_size):
        chunk = unique_results[i:i + page_size]
        page_lines = [f"🔗 <a href='{url}'>NFT Gift</a>\n👤 {owner}" for url, owner in chunk]
        page_content = "\n\n".join(page_lines)
        page_text = header_template + "<b>Список:</b>\n" + page_content
        result_pages.append(page_text)

    user_search_results[message.chat.id] = result_pages

    keyboard = create_pagination_keyboard(current_page=0, total_pages=len(result_pages), prefix="result_page")
    await message.answer(result_pages[0], reply_markup=keyboard, disable_web_page_preview=True)