"""Бизнес-логика приложения (use cases)."""

from __future__ import annotations

from datetime import datetime

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import (
    get_rate_from_cache,
    is_rate_fresh,
    validate_amount,
    validate_currency_code,
)
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self):
        """Инициализация сервиса."""
        self.db = DatabaseManager()

    @log_action("REGISTER")
    def register(self, username: str, password: str) -> User:
        """
        Зарегистрировать нового пользователя.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Созданный пользователь

        Raises:
            ValueError: Если имя занято или данные некорректны
        """
        # Проверяем уникальность
        users = self.db.read_users()
        if any(u["username"] == username for u in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        # Генерируем ID
        user_id = max([u["user_id"] for u in users], default=0) + 1

        # Создаем пользователя
        user = User.create_new(user_id, username, password)

        # Сохраняем
        users.append(user.to_dict())
        self.db.write_users(users)

        # Создаем пустой портфель
        portfolios = self.db.read_portfolios()
        portfolio = Portfolio(user_id)
        portfolios.append(portfolio.to_dict())
        self.db.write_portfolios(portfolios)

        return user

    @log_action("LOGIN")
    def login(self, username: str, password: str) -> User:
        """
        Войти в систему.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Пользователь

        Raises:
            ValueError: Если пользователь не найден или пароль неверный
        """
        users = self.db.read_users()
        user_data = next(
            (u for u in users if u["username"] == username), None
        )

        if not user_data:
            raise ValueError(f"Пользователь '{username}' не найден")

        user = User.from_dict(user_data)
        if not user.verify_password(password):
            raise ValueError("Неверный пароль")

        return user


class PortfolioService:
    """Сервис для работы с портфелями."""

    def __init__(self):
        """Инициализация сервиса."""
        self.db = DatabaseManager()
        self.settings = SettingsLoader()

    def get_portfolio(self, user_id: int) -> Portfolio | None:
        """
        Получить портфель пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Портфель или None
        """
        portfolios = self.db.read_portfolios()
        portfolio_data = next(
            (p for p in portfolios if p["user_id"] == user_id), None
        )

        if portfolio_data:
            return Portfolio.from_dict(portfolio_data)
        return None

    def save_portfolio(self, portfolio: Portfolio):
        """
        Сохранить портфель.

        Args:
            portfolio: Портфель для сохранения
        """
        portfolios = self.db.read_portfolios()
        # Обновляем или добавляем
        for i, p in enumerate(portfolios):
            if p["user_id"] == portfolio.user_id:
                portfolios[i] = portfolio.to_dict()
                break
        else:
            portfolios.append(portfolio.to_dict())

        self.db.write_portfolios(portfolios)

    @log_action("BUY")
    def buy(self, user_id: int, currency_code: str, amount: float) -> dict:
        """
        Купить валюту.

        Args:
            user_id: ID пользователя
            currency_code: Код валюты
            amount: Количество

        Returns:
            Информация о покупке
        """
        # Валидация
        code = validate_currency_code(currency_code)
        amount = validate_amount(amount)

        # Проверяем валюту
        get_currency(code)

        # Получаем портфель
        portfolio = self.get_portfolio(user_id)
        if not portfolio:
            raise ValueError("Портфель не найден")

        # Получаем или создаем кошелёк
        wallet = portfolio.get_wallet(code)
        if not wallet:
            wallet = portfolio.add_currency(code)

        # Сохраняем старый баланс для отчёта
        old_balance = wallet.balance

        # Пополняем
        wallet.deposit(amount)

        # Получаем курс для оценочной стоимости
        rates = self.db.read_rates()
        rate = get_rate_from_cache(code, "USD", rates)

        # Сохраняем портфель
        self.save_portfolio(portfolio)

        return {
            "currency": code,
            "amount": amount,
            "old_balance": old_balance,
            "new_balance": wallet.balance,
            "rate": rate,
            "estimated_cost": amount * rate if rate else None
        }

    @log_action("SELL")
    def sell(self, user_id: int, currency_code: str, amount: float) -> dict:
        """
        Продать валюту.

        Args:
            user_id: ID пользователя
            currency_code: Код валюты
            amount: Количество

        Returns:
            Информация о продаже
        """
        # Валидация
        code = validate_currency_code(currency_code)
        amount = validate_amount(amount)

        # Получаем портфель
        portfolio = self.get_portfolio(user_id)
        if not portfolio:
            raise ValueError("Портфель не найден")

        # Получаем кошелёк
        wallet = portfolio.get_wallet(code)
        if not wallet:
            raise ValueError(
                f"У вас нет кошелька '{code}'. Добавьте валюту: "
                f"она создаётся автоматически при первой покупке."
            )

        # Сохраняем старый баланс
        old_balance = wallet.balance

        # Снимаем средства (может выбросить InsufficientFundsError)
        wallet.withdraw(amount)

        # Получаем курс для оценочной выручки
        rates = self.db.read_rates()
        rate = get_rate_from_cache(code, "USD", rates)

        # Сохраняем портфель
        self.save_portfolio(portfolio)

        return {
            "currency": code,
            "amount": amount,
            "old_balance": old_balance,
            "new_balance": wallet.balance,
            "rate": rate,
            "estimated_revenue": amount * rate if rate else None
        }


class RateService:
    """Сервис для работы с курсами валют."""

    def __init__(self):
        """Инициализация сервиса."""
        self.db = DatabaseManager()
        self.settings = SettingsLoader()

    def get_rate(self, from_code: str, to_code: str) -> dict:
        """
        Получить курс валюты.

        Args:
            from_code: Исходная валюта
            to_code: Целевая валюта

        Returns:
            Информация о курсе

        Raises:
            CurrencyNotFoundError: Если валюта не найдена
            ApiRequestError: Если курс недоступен
        """
        # Валидация кодов
        from_currency = get_currency(from_code)
        to_currency = get_currency(to_code)

        from_upper = from_currency.code
        to_upper = to_currency.code

        # Одинаковые валюты
        if from_upper == to_upper:
            return {
                "from": from_upper,
                "to": to_upper,
                "rate": 1.0,
                "reverse_rate": 1.0,
                "updated_at": datetime.now().isoformat()
            }

        # Читаем кеш
        rates_cache = self.db.read_rates()
        pair_key = f"{from_upper}_{to_upper}"
        pairs = rates_cache.get("pairs", {})

        ttl = self.settings.get("RATES_TTL_SECONDS", 300)

        # Проверяем прямой курс
        if pair_key in pairs:
            pair_data = pairs[pair_key]
            rate = pair_data.get("rate")
            updated_at = pair_data.get("updated_at")

            if rate and updated_at:
                if is_rate_fresh(updated_at, ttl):
                    return {
                        "from": from_upper,
                        "to": to_upper,
                        "rate": rate,
                        "reverse_rate": 1.0 / rate if rate else None,
                        "updated_at": updated_at
                    }

        # Проверяем обратный курс
        reverse_key = f"{to_upper}_{from_upper}"
        if reverse_key in pairs:
            pair_data = pairs[reverse_key]
            reverse_rate = pair_data.get("rate")
            updated_at = pair_data.get("updated_at")

            if reverse_rate and reverse_rate != 0 and updated_at:
                if is_rate_fresh(updated_at, ttl):
                    rate = 1.0 / reverse_rate
                    return {
                        "from": from_upper,
                        "to": to_upper,
                        "rate": rate,
                        "reverse_rate": reverse_rate,
                        "updated_at": updated_at
                    }

        # Курс не найден или устарел
        raise ApiRequestError(
            f"Курс {from_upper}→{to_upper} недоступен. "
            f"Повторите попытку позже или выполните 'update-rates'."
        )

