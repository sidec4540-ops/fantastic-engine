import asyncio
import logging
import time
import database as db

class ProxyManager:
    def __init__(self, cooldown_seconds: int):
        self.proxies = []
        self.cooldown_seconds = cooldown_seconds
        self.cooldowns = {}
        self.current_index = 0
        self._lock = asyncio.Lock()

    async def load_proxies(self):
        logging.info("Загрузка списка прокси из БД...")
        self.proxies = await db.get_all_proxies()
        self.current_index = 0
        self.cooldowns = {}
        if not self.proxies:
            logging.warning("Список прокси пуст! Парсинг может не работать.")
        else:
            logging.info(f"Загружено {len(self.proxies)} прокси.")

    async def get_proxy(self) -> str | None:
        async with self._lock:
            if not self.proxies:
                return None
            start_index = self.current_index
            while True:
                proxy = self.proxies[self.current_index]
                cooldown_end_time = self.cooldowns.get(proxy, 0)
                if time.time() >= cooldown_end_time:
                    self.current_index = (self.current_index + 1) % len(self.proxies)
                    return proxy
                self.current_index = (self.current_index + 1) % len(self.proxies)
                if self.current_index == start_index:
                    logging.warning("Все прокси на кулдауне. Ожидание...")
                    await asyncio.sleep(self.cooldown_seconds)

    def report_failure(self, proxy: str):
        self.cooldowns[proxy] = time.time() + self.cooldown_seconds
        proxy_display = proxy.split('@')[-1] if '@' in proxy else proxy
        logging.warning(f"Прокси {proxy_display} отправлен на отдых на {self.cooldown_seconds} сек.")

proxy_manager = ProxyManager(cooldown_seconds=30)