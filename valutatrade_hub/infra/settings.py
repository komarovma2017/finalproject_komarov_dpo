"""Singleton для управления конфигурацией приложения."""

from pathlib import Path
from typing import Any


class SettingsLoader:
    """
    Singleton для загрузки и кеширования конфигурации проекта.

    Реализован через __new__ для простоты и читаемости.
    Гарантирует единственный экземпляр во всем приложении.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Создает или возвращает существующий экземпляр."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализирует настройки (выполняется только один раз)."""
        if not self._initialized:
            self._load_settings()
            SettingsLoader._initialized = True

    def _load_settings(self):
        """Загружает настройки из конфигурации."""
        # Базовая директория проекта
        base_dir = Path(__file__).parent.parent.parent

        # Настройки по умолчанию
        self._settings = {
            # Пути к файлам данных
            "DATA_DIR": str(base_dir / "data"),
            "USERS_FILE": str(base_dir / "data" / "users.json"),
            "PORTFOLIOS_FILE": str(base_dir / "data" / "portfolios.json"),
            "RATES_FILE": str(base_dir / "data" / "rates.json"),
            "EXCHANGE_RATES_FILE": str(
                base_dir / "data" / "exchange_rates.json"
            ),

            # Логирование
            "LOG_FILE": str(base_dir / "logs" / "actions.log"),
            "LOG_LEVEL": "INFO",

            # Настройки курсов валют
            "RATES_TTL_SECONDS": 300,  # 5 минут
            "DEFAULT_BASE_CURRENCY": "USD",

            # API настройки
            "REQUEST_TIMEOUT": 10,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение настройки по ключу.

        Args:
            key: Ключ настройки
            default: Значение по умолчанию

        Returns:
            Значение настройки или default
        """
        return self._settings.get(key, default)

    def reload(self):
        """Перезагружает конфигурацию."""
        self._load_settings()

    @classmethod
    def reset(cls):
        """Сбрасывает singleton (для тестирования)."""
        cls._instance = None
        cls._initialized = False

