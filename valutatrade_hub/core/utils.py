"""Вспомогательные функции для работы с валютами и данными."""

from __future__ import annotations

from datetime import datetime, timedelta

from valutatrade_hub.core.currencies import get_currency


def validate_currency_code(code: str) -> str:
    """
    Валидировать код валюты.

    Args:
        code: Код валюты

    Returns:
        Код валюты в верхнем регистре

    Raises:
        CurrencyNotFoundError: Если валюта не найдена
    """
    if not code or not isinstance(code, str):
        raise ValueError("Код валюты должен быть непустой строкой")

    code_upper = code.upper()
    # Проверяем, что валюта существует в реестре
    get_currency(code_upper)
    return code_upper


def validate_amount(amount: float) -> float:
    """
    Валидировать сумму операции.

    Args:
        amount: Сумма

    Returns:
        Валидированная сумма

    Raises:
        ValueError: Если сумма некорректна
    """
    if not isinstance(amount, (int, float)):
        raise TypeError("'amount' должен быть числом")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return float(amount)


def is_rate_fresh(updated_at: str, ttl_seconds: int) -> bool:
    """
    Проверить, является ли курс актуальным.

    Args:
        updated_at: Время последнего обновления (ISO формат)
        ttl_seconds: Срок годности в секундах

    Returns:
        True, если курс свежий
    """
    try:
        last_update = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if last_update.tzinfo:
            now = datetime.now(last_update.tzinfo)
        else:
            now = datetime.now()
        age = now - last_update
        return age < timedelta(seconds=ttl_seconds)
    except (ValueError, AttributeError):
        return False


def format_currency_amount(amount: float, decimals: int = 4) -> str:
    """
    Форматировать сумму валюты для отображения.

    Args:
        amount: Сумма
        decimals: Количество десятичных знаков

    Returns:
        Отформатированная строка
    """
    return f"{amount:.{decimals}f}"


def get_rate_from_cache(
    from_code: str,
    to_code: str,
    rates_cache: dict
) -> float | None:
    """
    Получить курс из кеша.

    Args:
        from_code: Исходная валюта
        to_code: Целевая валюта
        rates_cache: Кеш курсов

    Returns:
        Курс или None, если не найден
    """
    pair_key = f"{from_code.upper()}_{to_code.upper()}"
    pairs = rates_cache.get("pairs", {})

    if pair_key in pairs:
        return pairs[pair_key].get("rate")

    # Попробуем обратный курс
    reverse_key = f"{to_code.upper()}_{from_code.upper()}"
    if reverse_key in pairs:
        reverse_rate = pairs[reverse_key].get("rate")
        if reverse_rate and reverse_rate != 0:
            return 1.0 / reverse_rate

    return None


def calculate_conversion(
    amount: float,
    from_code: str,
    to_code: str,
    rates_cache: dict
) -> float | None:
    """
    Вычислить конвертацию валюты.

    Args:
        amount: Сумма для конвертации
        from_code: Исходная валюта
        to_code: Целевая валюта
        rates_cache: Кеш курсов

    Returns:
        Конвертированная сумма или None
    """
    if from_code.upper() == to_code.upper():
        return amount

    rate = get_rate_from_cache(from_code, to_code, rates_cache)
    if rate:
        return amount * rate

    return None

