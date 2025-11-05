"""Singleton для управления JSON-хранилищем данных."""

import json
import os
from typing import Any

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """
    Singleton для работы с JSON-файлами.

    Предоставляет унифицированный интерфейс для чтения/записи данных.
    Реализован через __new__ для обеспечения единственности экземпляра.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Создает или возвращает существующий экземпляр."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализирует менеджер БД (выполняется только один раз)."""
        if not self._initialized:
            self.settings = SettingsLoader()
            self._ensure_data_files()
            DatabaseManager._initialized = True

    def _ensure_data_files(self):
        """Создает директории и файлы данных, если их нет."""
        data_dir = self.settings.get("DATA_DIR")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

        # Инициализируем пустые файлы, если их нет
        files_defaults = {
            self.settings.get("USERS_FILE"): [],
            self.settings.get("PORTFOLIOS_FILE"): [],
            self.settings.get("RATES_FILE"): {
                "pairs": {},
                "last_refresh": None
            },
            self.settings.get("EXCHANGE_RATES_FILE"): []
        }

        for filepath, default_content in files_defaults.items():
            if not os.path.exists(filepath):
                self._write_json(filepath, default_content)

    def _read_json(self, filepath: str) -> Any:
        """
        Читает данные из JSON файла.

        Args:
            filepath: Путь к файлу

        Returns:
            Данные из файла
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _write_json(self, filepath: str, data: Any):
        """
        Записывает данные в JSON файл.

        Args:
            filepath: Путь к файлу
            data: Данные для записи
        """
        # Атомарная запись через временный файл
        temp_file = filepath + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Переименование в целевой файл
        os.replace(temp_file, filepath)

    def read_users(self) -> list:
        """Читает список пользователей."""
        return self._read_json(self.settings.get("USERS_FILE")) or []

    def write_users(self, users: list):
        """Записывает список пользователей."""
        self._write_json(self.settings.get("USERS_FILE"), users)

    def read_portfolios(self) -> list:
        """Читает список портфелей."""
        return self._read_json(self.settings.get("PORTFOLIOS_FILE")) or []

    def write_portfolios(self, portfolios: list):
        """Записывает список портфелей."""
        self._write_json(self.settings.get("PORTFOLIOS_FILE"), portfolios)

    def read_rates(self) -> dict:
        """Читает кеш курсов валют."""
        default = {"pairs": {}, "last_refresh": None}
        return self._read_json(self.settings.get("RATES_FILE")) or default

    def write_rates(self, rates: dict):
        """Записывает кеш курсов валют."""
        self._write_json(self.settings.get("RATES_FILE"), rates)

    def read_exchange_rates(self) -> list:
        """Читает историю курсов валют."""
        return (
            self._read_json(self.settings.get("EXCHANGE_RATES_FILE")) or []
        )

    def write_exchange_rates(self, rates: list):
        """Записывает историю курсов валют."""
        self._write_json(self.settings.get("EXCHANGE_RATES_FILE"), rates)

    @classmethod
    def reset(cls):
        """Сбрасывает singleton (для тестирования)."""
        cls._instance = None
        cls._initialized = False

