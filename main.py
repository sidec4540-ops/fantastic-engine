import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
import database as db
from middlewares.access import AccessMiddleware
from services.proxy_manager import proxy_manager

from handlers import user_handlers, admin_handlers, fsm_handlers

async def main() -> None:
    await db.init_db()
    await proxy_manager.load_proxies()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())

    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    dp.include_router(fsm_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())