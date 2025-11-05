"""Иерархия валют с базовым абстрактным классом и наследниками."""

from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактный базовый класс для валют.

    Определяет общий интерфейс для всех типов валют.
    """

    def __init__(self, name: str, code: str):
        """
        Инициализация валюты.

        Args:
            name: Полное имя валюты
            code: Код валюты (ISO или тикер)
        """
        self._validate_code(code)
        self._validate_name(name)
        self.name = name
        self.code = code.upper()

    @staticmethod
    def _validate_code(code: str):
        """Валидация кода валюты."""
        if not code or not isinstance(code, str):
            raise ValueError("Код валюты должен быть непустой строкой")
        if not (2 <= len(code) <= 5):
            raise ValueError("Код валюты должен быть длиной от 2 до 5 символов")
        if not code.replace("_", "").isalpha():
            raise ValueError("Код валюты должен содержать только буквы")

    @staticmethod
    def _validate_name(name: str):
        """Валидация имени валюты."""
        if not name or not isinstance(name, str):
            raise ValueError("Имя валюты должно быть непустой строкой")

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает строковое представление для UI и логов.

        Returns:
            Отформатированная строка с информацией о валюте
        """


class FiatCurrency(Currency):
    """Фиатная валюта (государственная)."""

    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализация фиатной валюты.

        Args:
            name: Полное имя валюты
            code: Код валюты
            issuing_country: Страна или зона эмиссии
        """
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        """Возвращает информацию о фиатной валюте."""
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


class CryptoCurrency(Currency):
    """Криптовалюта."""

    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float = 0.0
    ):
        """
        Инициализация криптовалюты.

        Args:
            name: Полное имя валюты
            code: Код валюты
            algorithm: Алгоритм консенсуса
            market_cap: Рыночная капитализация
        """
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        """Возвращает информацию о криптовалюте."""
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# Реестр поддерживаемых валют
_CURRENCY_REGISTRY = {
    # Фиатные валюты
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russian Federation"),

    # Криптовалюты
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
    "SOL": CryptoCurrency("Solana", "SOL", "PoH", 7.8e10),
}


def get_currency(code: str) -> Currency:
    """
    Получить валюту по коду из реестра.

    Args:
        code: Код валюты

    Returns:
        Объект валюты

    Raises:
        CurrencyNotFoundError: Если валюта не найдена
    """
    code_upper = code.upper()
    if code_upper not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    return _CURRENCY_REGISTRY[code_upper]


def get_all_currencies() -> dict:
    """
    Получить все поддерживаемые валюты.

    Returns:
        Словарь всех валют
    """
    return _CURRENCY_REGISTRY.copy()

