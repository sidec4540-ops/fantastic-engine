import aiosqlite
import logging

DB_FILE = 'bot_database.db'

async def init_db():
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS proxies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_str TEXT NOT NULL UNIQUE
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS blocked_users (
                    user_id INTEGER PRIMARY KEY
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    username TEXT PRIMARY KEY
                )
            ''')
            await db.commit()
            logging.info("База данных успешно инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации БД: {e}")

async def add_proxy(proxy_str: str) -> bool:
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("INSERT INTO proxies (proxy_str) VALUES (?)", (proxy_str,))
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False
    except Exception as e:
        logging.error(f"Ошибка при добавлении прокси {proxy_str}: {e}")
        return False

async def delete_proxy(proxy_str: str) -> bool:
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("DELETE FROM proxies WHERE proxy_str = ?", (proxy_str,))
            await db.commit()
            return db.total_changes > 0
    except Exception as e:
        logging.error(f"Ошибка при удалении прокси {proxy_str}: {e}")
        return False

async def get_all_proxies() -> list[str]:
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT proxy_str FROM proxies") as cursor:
                return [row[0] for row in await cursor.fetchall()]
    except Exception as e:
        logging.error(f"Ошибка при получении списка прокси: {e}")
        return []

async def set_subscription_channel(channel_username: str | None):
    key = "subscription_channel"
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            if channel_username:
                await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, channel_username))
            else:
                await db.execute("DELETE FROM settings WHERE key = ?", (key,))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при установке канала подписки: {e}")

async def get_subscription_channel() -> str | None:
    key = "subscription_channel"
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        logging.error(f"Ошибка при получении канала подписки: {e}")
        return None

async def block_user(user_id: int):
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)", (user_id,))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при блокировке пользователя {user_id}: {e}")

async def unblock_user(user_id: int):
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id,))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при разблокировке пользователя {user_id}: {e}")

async def is_user_blocked(user_id: int) -> bool:
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT 1 FROM blocked_users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone() is not None
    except Exception as e:
        logging.error(f"Ошибка при проверке блокировки {user_id}: {e}")
        return False

async def add_to_blacklist(username: str):
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("INSERT OR IGNORE INTO blacklist (username) VALUES (?)", (username.lower(),))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при добавлении в ЧС {username}: {e}")

async def remove_from_blacklist(username: str):
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("DELETE FROM blacklist WHERE username = ?", (username.lower(),))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при удалении из ЧС {username}: {e}")

async def get_blacklist() -> list[str]:
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT username FROM blacklist") as cursor:
                return [row[0] for row in await cursor.fetchall()]
    except Exception as e:
        logging.error(f"Ошибка при получении ЧС: {e}")
        return []