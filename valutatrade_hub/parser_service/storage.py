"""Хранилище для Parser Service."""

import logging
from datetime import datetime

from valutatrade_hub.infra.database import DatabaseManager


class RatesStorage:
    """Класс для работы с хранилищем курсов."""

    def __init__(self):
        """Инициализация хранилища."""
        self.db = DatabaseManager()
        self.logger = logging.getLogger(self.__class__.__name__)

    def save_rates(self, rates: dict, source: str):
        """
        Сохранить курсы в кеш и историю.

        Args:
            rates: Словарь курсов {pair_key: rate}
            source: Источник данных
        """
        timestamp = datetime.now().isoformat()

        # Обновляем кеш (rates.json)
        self._update_cache(rates, timestamp, source)

        # Сохраняем в историю (exchange_rates.json)
        self._save_to_history(rates, timestamp, source)

    def _update_cache(self, rates: dict, timestamp: str, source: str):
        """
        Обновить кеш курсов.

        Args:
            rates: Курсы валют
            timestamp: Время обновления
            source: Источник
        """
        cache = self.db.read_rates()

        if "pairs" not in cache:
            cache["pairs"] = {}

        # Обновляем пары
        for pair_key, rate in rates.items():
            cache["pairs"][pair_key] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": source
            }

        cache["last_refresh"] = timestamp
        self.db.write_rates(cache)
        self.logger.info(f"Updated cache with {len(rates)} rates")

    def _save_to_history(self, rates: dict, timestamp: str, source: str):
        """
        Сохранить курсы в историю.

        Args:
            rates: Курсы валют
            timestamp: Время
            source: Источник
        """
        history = self.db.read_exchange_rates()

        # Добавляем новые записи
        for pair_key, rate in rates.items():
            from_curr, to_curr = pair_key.split("_")
            record_id = f"{pair_key}_{timestamp}"

            # Проверяем, нет ли уже такой записи
            if any(r.get("id") == record_id for r in history):
                continue

            record = {
                "id": record_id,
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": rate,
                "timestamp": timestamp,
                "source": source
            }
            history.append(record)

        self.db.write_exchange_rates(history)
        self.logger.info(f"Saved {len(rates)} records to history")

