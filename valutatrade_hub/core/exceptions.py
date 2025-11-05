"""Пользовательские исключения для приложения."""


class InsufficientFundsError(Exception):
    """Исключение при недостаточности средств на счету."""

    def __init__(self, available: float, required: float, code: str):
        """
        Инициализация исключения.

        Args:
            available: Доступная сумма
            required: Требуемая сумма
            code: Код валюты
        """
        self.available = available
        self.required = required
        self.code = code
        message = (
            f"Недостаточно средств: доступно {available} {code}, "
            f"требуется {required} {code}"
        )
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Исключение при обращении к неизвестной валюте."""

    def __init__(self, code: str):
        """
        Инициализация исключения.

        Args:
            code: Код валюты
        """
        self.code = code
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    """Исключение при ошибках обращения к внешнему API."""

    def __init__(self, reason: str):
        """
        Инициализация исключения.

        Args:
            reason: Причина ошибки
        """
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)

