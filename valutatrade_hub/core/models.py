"""Основные модели данных: User, Wallet, Portfolio."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime | None = None
    ):
        """
        Инициализация пользователя.

        Args:
            user_id: Уникальный идентификатор
            username: Имя пользователя
            hashed_password: Хешированный пароль
            salt: Соль для хеширования
            registration_date: Дата регистрации
        """
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = (
            registration_date or datetime.now()
        )

    @property
    def user_id(self) -> int:
        """Получить ID пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Получить имя пользователя."""
        return self._username

    @username.setter
    def username(self, value: str):
        """Установить имя пользователя."""
        if not value or not isinstance(value, str):
            raise ValueError("Имя не может быть пустым")
        self._username = value

    @property
    def registration_date(self) -> datetime:
        """Получить дату регистрации."""
        return self._registration_date

    def get_user_info(self) -> dict:
        """
        Получить информацию о пользователе (без пароля).

        Returns:
            Словарь с информацией о пользователе
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat()
        }

    def change_password(self, new_password: str):
        """
        Изменить пароль пользователя.

        Args:
            new_password: Новый пароль
        """
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        # Генерируем новую соль и хешируем пароль
        self._salt = secrets.token_hex(8)
        self._hashed_password = self._hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        """
        Проверить пароль.

        Args:
            password: Пароль для проверки

        Returns:
            True, если пароль верный
        """
        hashed = self._hash_password(password, self._salt)
        return hashed == self._hashed_password

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """
        Хеширование пароля с солью.

        Args:
            password: Пароль
            salt: Соль

        Returns:
            Хеш пароля
        """
        combined = (password + salt).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    @classmethod
    def create_new(cls, user_id: int, username: str, password: str) -> User:
        """
        Создать нового пользователя.

        Args:
            user_id: ID пользователя
            username: Имя пользователя
            password: Пароль

        Returns:
            Новый объект User
        """
        if not username:
            raise ValueError("Имя не может быть пустым")
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        salt = secrets.token_hex(8)
        hashed_password = cls._hash_password(password, salt)

        return cls(user_id, username, hashed_password, salt)

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> User:
        """Десериализация из словаря."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(
                data["registration_date"]
            )
        )


class Wallet:
    """Кошелёк для одной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Инициализация кошелька.

        Args:
            currency_code: Код валюты
            balance: Начальный баланс
        """
        self.currency_code = currency_code.upper()
        self._balance = 0.0
        self.balance = balance  # Используем setter для валидации

    @property
    def balance(self) -> float:
        """Получить баланс."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Установить баланс."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float):
        """
        Пополнить баланс.

        Args:
            amount: Сумма пополнения
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        self._balance += amount

    def withdraw(self, amount: float):
        """
        Снять средства.

        Args:
            amount: Сумма снятия
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self._balance:
            from valutatrade_hub.core.exceptions import InsufficientFundsError
            raise InsufficientFundsError(
                self._balance, amount, self.currency_code
            )
        self._balance -= amount

    def get_balance_info(self) -> str:
        """
        Получить информацию о балансе.

        Returns:
            Строка с информацией о балансе
        """
        return f"{self.currency_code}: {self._balance:.4f}"

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }

    @classmethod
    def from_dict(cls, data: dict) -> Wallet:
        """Десериализация из словаря."""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )


class Portfolio:
    """Портфель пользователя с множеством кошельков."""

    def __init__(self, user_id: int, wallets: dict | None = None):
        """
        Инициализация портфеля.

        Args:
            user_id: ID пользователя
            wallets: Словарь кошельков
        """
        self._user_id = user_id
        self._wallets = wallets or {}

    @property
    def user_id(self) -> int:
        """Получить ID пользователя."""
        return self._user_id

    @property
    def wallets(self) -> dict:
        """Получить копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавить новую валюту в портфель.

        Args:
            currency_code: Код валюты

        Returns:
            Созданный кошелёк
        """
        code_upper = currency_code.upper()
        if code_upper in self._wallets:
            raise ValueError(f"Кошелёк {code_upper} уже существует")

        wallet = Wallet(code_upper)
        self._wallets[code_upper] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """
        Получить кошелёк по коду валюты.

        Args:
            currency_code: Код валюты

        Returns:
            Кошелёк или None
        """
        return self._wallets.get(currency_code.upper())

    def get_total_value(
        self,
        exchange_rates: dict,
        base_currency: str = "USD"
    ) -> float:
        """
        Вычислить общую стоимость портфеля в базовой валюте.

        Args:
            exchange_rates: Курсы валют
            base_currency: Базовая валюта

        Returns:
            Общая стоимость
        """
        total = 0.0
        base_upper = base_currency.upper()

        for code, wallet in self._wallets.items():
            if code == base_upper:
                total += wallet.balance
            else:
                # Ищем курс валюты к базовой
                pair_key = f"{code}_{base_upper}"
                if pair_key in exchange_rates:
                    rate = exchange_rates[pair_key]
                    total += wallet.balance * rate
                else:
                    # Если прямого курса нет, считаем как 0
                    pass

        return total

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        wallets_dict = {
            code: wallet.to_dict() for code, wallet in self._wallets.items()
        }
        return {
            "user_id": self._user_id,
            "wallets": wallets_dict
        }

    @classmethod
    def from_dict(cls, data: dict) -> Portfolio:
        """Десериализация из словаря."""
        wallets = {}
        for code, wallet_data in data.get("wallets", {}).items():
            wallets[code] = Wallet.from_dict(wallet_data)

        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )

