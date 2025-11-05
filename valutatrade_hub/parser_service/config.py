"""Конфигурация Parser Service."""

import os
from dataclasses import dataclass


@dataclass
class ParserConfig:
    """Настройки Parser Service."""

    # Ключ загружается из переменной окружения
    EXCHANGERATE_API_KEY: str = os.getenv(
        "EXCHANGERATE_API_KEY", "demo-key"
    )

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Списки валют
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP: dict = None

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10

    def __post_init__(self):
        """Инициализация после создания объекта."""
        if self.CRYPTO_ID_MAP is None:
            self.CRYPTO_ID_MAP = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
            }

