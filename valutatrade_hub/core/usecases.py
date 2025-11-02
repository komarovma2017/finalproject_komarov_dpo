"""Бизнес-логика приложения."""

from datetime import datetime
from typing import Optional

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import (
    DataStorage,
    format_currency,
    get_rate_key,
    validate_amount,
    validate_currency_code,
)


class AuthService:
    """Сервис аутентификации и управления пользователями."""

    def __init__(self, storage: DataStorage):
        """
        Инициализация сервиса.

        Args:
            storage: Хранилище данных
        """
        self.storage = storage
        self.current_user: Optional[User] = None

    def register_user(
        self, username: str, password: str
    ) -> tuple[bool, str, Optional[int]]:
        """
        Зарегистрировать нового пользователя.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Кортеж (успех, сообщение, user_id)
        """
        # Валидация
        if not username or not username.strip():
            return False, "Имя пользователя не может быть пустым", None

        if len(password) < 4:
            return False, "Пароль должен быть не короче 4 символов", None

        # Проверка уникальности
        if self.storage.find_user_by_username(username):
            return False, f"Имя пользователя '{username}' уже занято", None

        # Создание пользователя
        user_id = self.storage.get_next_user_id()
        user = User(
            user_id=user_id,
            username=username,
            password=password,
            registration_date=datetime.now(),
        )

        # Сохранение пользователя
        users = self.storage.load_users()
        users.append(user.to_dict())
        self.storage.save_users(users)

        # Создание пустого портфеля
        portfolio = Portfolio(user_id=user_id)
        portfolios = self.storage.load_portfolios()
        portfolios.append(portfolio.to_dict())
        self.storage.save_portfolios(portfolios)

        message = (
            f"Пользователь '{username}' зарегистрирован (id={user_id}). "
            f"Войдите: login --username {username} --password ****"
        )
        return True, message, user_id

    def login_user(self, username: str, password: str) -> tuple[bool, str]:
        """
        Войти в систему.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Кортеж (успех, сообщение)
        """
        user_data = self.storage.find_user_by_username(username)

        if not user_data:
            return False, f"Пользователь '{username}' не найден"

        # Загрузка пользователя
        user = User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            hashed_password=user_data["hashed_password"],
            salt=user_data["salt"],
            registration_date=datetime.fromisoformat(
                user_data["registration_date"]
            ),
        )

        # Проверка пароля
        if not user.verify_password(password):
            return False, "Неверный пароль"

        self.current_user = user
        return True, f"Вы вошли как '{username}'"

    def logout(self) -> None:
        """Выйти из системы."""
        self.current_user = None

    def is_logged_in(self) -> bool:
        """
        Проверить, залогинен ли пользователь.

        Returns:
            True если залогинен
        """
        return self.current_user is not None

    def get_current_user(self) -> Optional[User]:
        """
        Получить текущего пользователя.

        Returns:
            Текущий пользователь или None
        """
        return self.current_user


class PortfolioService:
    """Сервис управления портфелями."""

    def __init__(self, storage: DataStorage, auth_service: AuthService):
        """
        Инициализация сервиса.

        Args:
            storage: Хранилище данных
            auth_service: Сервис аутентификации
        """
        self.storage = storage
        self.auth_service = auth_service

    def _load_user_portfolio(self) -> Optional[Portfolio]:
        """
        Загрузить портфель текущего пользователя.

        Returns:
            Портфель или None
        """
        user = self.auth_service.get_current_user()
        if not user:
            return None

        portfolio_data = self.storage.find_portfolio_by_user_id(user.user_id)
        if not portfolio_data:
            return None

        return Portfolio(
            user_id=portfolio_data["user_id"],
            wallets=portfolio_data.get("wallets", {}),
        )

    def _save_portfolio(self, portfolio: Portfolio) -> None:
        """
        Сохранить портфель.

        Args:
            portfolio: Портфель для сохранения
        """
        portfolios = self.storage.load_portfolios()

        # Найти и обновить портфель
        for i, p in enumerate(portfolios):
            if p["user_id"] == portfolio.user_id:
                portfolios[i] = portfolio.to_dict()
                break

        self.storage.save_portfolios(portfolios)

    def show_portfolio(self, base_currency: str = "USD") -> tuple[bool, str]:
        """
        Показать портфель пользователя.

        Args:
            base_currency: Базовая валюта для конвертации

        Returns:
            Кортеж (успех, сообщение)
        """
        if not self.auth_service.is_logged_in():
            return False, "Сначала выполните login"

        user = self.auth_service.get_current_user()
        portfolio = self._load_user_portfolio()

        if not portfolio:
            return False, "Портфель не найден"

        base_currency = validate_currency_code(base_currency)

        # Загрузка курсов
        rates = self.storage.load_rates()

        wallets = portfolio.wallets
        if not wallets:
            return True, f"Портфель пользователя '{user.username}' пуст"

        # Формирование отчета
        lines = [
            f"Портфель пользователя '{user.username}' "
            f"(база: {base_currency}):"
        ]

        total_value = 0.0
        for currency_code, wallet in sorted(wallets.items()):
            balance = wallet.balance

            # Конвертация в базовую валюту
            if currency_code == base_currency:
                value_in_base = balance
            else:
                rate_key = get_rate_key(currency_code, base_currency)
                rate_data = rates.get(rate_key)
                if rate_data:
                    rate = rate_data.get("rate", 0)
                    value_in_base = balance * rate
                else:
                    # Если курс не найден, пытаемся обратный курс
                    reverse_key = get_rate_key(base_currency, currency_code)
                    reverse_data = rates.get(reverse_key)
                    if reverse_data:
                        reverse_rate = reverse_data.get("rate", 0)
                        if reverse_rate > 0:
                            value_in_base = balance / reverse_rate
                        else:
                            value_in_base = 0
                    else:
                        value_in_base = 0

            total_value += value_in_base

            # Форматирование строки
            if currency_code in ("BTC", "ETH"):
                balance_str = f"{balance:.4f}"
            else:
                balance_str = f"{balance:.2f}"

            lines.append(
                f"- {currency_code}: {balance_str}  → "
                f"{format_currency(value_in_base, base_currency)}"
            )

        lines.append("-" * 33)
        lines.append(f"ИТОГО: {format_currency(total_value, base_currency)}")

        return True, "\n".join(lines)

    def buy_currency(self, currency: str, amount: float) -> tuple[bool, str]:
        """
        Купить валюту.

        Args:
            currency: Код валюты
            amount: Количество

        Returns:
            Кортеж (успех, сообщение)
        """
        if not self.auth_service.is_logged_in():
            return False, "Сначала выполните login"

        try:
            currency = validate_currency_code(currency)
            amount = validate_amount(amount)
        except ValueError as e:
            return False, str(e)

        portfolio = self._load_user_portfolio()
        if not portfolio:
            return False, "Портфель не найден"

        # Получение или создание кошелька
        wallet = portfolio.get_or_create_wallet(currency)
        old_balance = wallet.balance

        # Пополнение
        wallet.deposit(amount)
        new_balance = wallet.balance

        # Сохранение
        self._save_portfolio(portfolio)

        # Расчет стоимости покупки
        rates = self.storage.load_rates()
        rate_key = get_rate_key(currency, "USD")
        rate_data = rates.get(rate_key)

        lines = []
        if rate_data:
            rate = rate_data.get("rate", 0)
            cost = amount * rate
            lines.append(
                f"Покупка выполнена: {amount:.4f} {currency} "
                f"по курсу {rate:,.2f} USD/{currency}"
            )
        else:
            lines.append(f"Покупка выполнена: {amount:.4f} {currency}")

        lines.append("Изменения в портфеле:")
        lines.append(
            f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}"
        )

        if rate_data:
            lines.append(
                f"Оценочная стоимость покупки: "
                f"{format_currency(cost, 'USD')}"
            )

        return True, "\n".join(lines)

    def sell_currency(self, currency: str, amount: float) -> tuple[bool, str]:
        """
        Продать валюту.

        Args:
            currency: Код валюты
            amount: Количество

        Returns:
            Кортеж (успех, сообщение)
        """
        if not self.auth_service.is_logged_in():
            return False, "Сначала выполните login"

        try:
            currency = validate_currency_code(currency)
            amount = validate_amount(amount)
        except ValueError as e:
            return False, str(e)

        portfolio = self._load_user_portfolio()
        if not portfolio:
            return False, "Портфель не найден"

        # Проверка существования кошелька
        wallet = portfolio.get_wallet(currency)
        if not wallet:
            msg = (
                f"У вас нет кошелька '{currency}'. Добавьте валюту: "
                f"она создаётся автоматически при первой покупке."
            )
            return False, msg

        old_balance = wallet.balance

        # Снятие
        try:
            wallet.withdraw(amount)
        except ValueError as e:
            return False, str(e)

        new_balance = wallet.balance

        # Сохранение
        self._save_portfolio(portfolio)

        # Расчет выручки
        rates = self.storage.load_rates()
        rate_key = get_rate_key(currency, "USD")
        rate_data = rates.get(rate_key)

        lines = []
        if rate_data:
            rate = rate_data.get("rate", 0)
            revenue = amount * rate
            lines.append(
                f"Продажа выполнена: {amount:.4f} {currency} "
                f"по курсу {rate:,.2f} USD/{currency}"
            )
        else:
            lines.append(f"Продажа выполнена: {amount:.4f} {currency}")

        lines.append("Изменения в портфеле:")
        lines.append(
            f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}"
        )

        if rate_data:
            lines.append(
                f"Оценочная выручка: {format_currency(revenue, 'USD')}"
            )

        return True, "\n".join(lines)


class RateService:
    """Сервис получения курсов валют."""

    def __init__(self, storage: DataStorage):
        """
        Инициализация сервиса.

        Args:
            storage: Хранилище данных
        """
        self.storage = storage

    def get_rate(
        self, from_currency: str, to_currency: str
    ) -> tuple[bool, str]:
        """
        Получить курс валют.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта

        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            from_currency = validate_currency_code(from_currency)
            to_currency = validate_currency_code(to_currency)
        except ValueError as e:
            return False, str(e)

        rates = self.storage.load_rates()
        rate_key = get_rate_key(from_currency, to_currency)

        rate_data = rates.get(rate_key)
        if not rate_data:
            # Попытка найти обратный курс
            reverse_key = get_rate_key(to_currency, from_currency)
            reverse_data = rates.get(reverse_key)

            if reverse_data:
                reverse_rate = reverse_data.get("rate", 0)
                if reverse_rate > 0:
                    rate = 1 / reverse_rate
                    updated_at = reverse_data.get("updated_at", "неизвестно")

                    lines = [
                        f"Курс {from_currency}→{to_currency}: {rate:.8f} "
                        f"(обновлено: {updated_at})",
                        f"Обратный курс {to_currency}→{from_currency}: "
                        f"{reverse_rate:,.2f}",
                    ]
                    return True, "\n".join(lines)

            msg = (
                f"Курс {from_currency}→{to_currency} недоступен. "
                f"Повторите попытку позже."
            )
            return False, msg

        rate = rate_data.get("rate", 0)
        updated_at = rate_data.get("updated_at", "неизвестно")

        # Вычисление обратного курса
        reverse_rate = 1 / rate if rate > 0 else 0

        lines = [
            f"Курс {from_currency}→{to_currency}: {rate:.8f} "
            f"(обновлено: {updated_at})",
            f"Обратный курс {to_currency}→{from_currency}: "
            f"{reverse_rate:,.2f}",
        ]

        return True, "\n".join(lines)
