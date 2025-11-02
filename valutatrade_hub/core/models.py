"""Модели данных для системы торговли валютами."""

import hashlib
import secrets
from datetime import datetime
from typing import Optional


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        password: Optional[str] = None,
        hashed_password: Optional[str] = None,
        salt: Optional[str] = None,
        registration_date: Optional[datetime] = None,
    ):
        """
        Инициализация пользователя.

        Args:
            user_id: Уникальный идентификатор пользователя
            username: Имя пользователя
            password: Пароль (будет захеширован)
            hashed_password: Уже захешированный пароль
            salt: Соль для хеширования
            registration_date: Дата регистрации
        """
        self._user_id = user_id
        self._username = username
        self._registration_date = registration_date or datetime.now()

        if password and not hashed_password:
            # Создаем нового пользователя с паролем
            self._salt = secrets.token_hex(8)
            self._hashed_password = self._hash_password(password, self._salt)
        elif hashed_password and salt:
            # Загружаем существующего пользователя
            self._salt = salt
            self._hashed_password = hashed_password
        else:
            msg = "Необходимо указать password или (hashed_password и salt)"
            raise ValueError(msg)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Хеширование пароля с солью."""
        combined = (password + salt).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    @property
    def user_id(self) -> int:
        """Получить ID пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Получить имя пользователя."""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        """Установить имя пользователя."""
        if not value or not value.strip():
            msg = "Имя пользователя не может быть пустым"
            raise ValueError(msg)
        self._username = value.strip()

    @property
    def registration_date(self) -> datetime:
        """Получить дату регистрации."""
        return self._registration_date

    @property
    def hashed_password(self) -> str:
        """Получить захешированный пароль."""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Получить соль."""
        return self._salt

    def get_user_info(self) -> dict:
        """
        Получить информацию о пользователе без пароля.

        Returns:
            Словарь с информацией о пользователе
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        """
        Изменить пароль пользователя.

        Args:
            new_password: Новый пароль

        Raises:
            ValueError: Если пароль короче 4 символов
        """
        if len(new_password) < 4:
            msg = "Пароль должен быть не короче 4 символов"
            raise ValueError(msg)

        self._salt = secrets.token_hex(8)
        self._hashed_password = self._hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        """
        Проверить пароль.

        Args:
            password: Пароль для проверки

        Returns:
            True если пароль верный, иначе False
        """
        return self._hashed_password == self._hash_password(
            password, self._salt
        )

    def to_dict(self) -> dict:
        """Конвертировать пользователя в словарь для сохранения."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }


class Wallet:
    """Класс кошелька для одной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Инициализация кошелька.

        Args:
            currency_code: Код валюты (USD, BTC, EUR и т.д.)
            balance: Начальный баланс
        """
        self.currency_code = currency_code.upper()
        self._balance = 0.0
        self.balance = balance  # Используем setter для валидации

    @property
    def balance(self) -> float:
        """Получить текущий баланс."""
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        """
        Установить баланс.

        Args:
            value: Новое значение баланса

        Raises:
            ValueError: Если баланс отрицательный или некорректного типа
        """
        if not isinstance(value, (int, float)):
            msg = "Баланс должен быть числом"
            raise TypeError(msg)
        if value < 0:
            msg = "Баланс не может быть отрицательным"
            raise ValueError(msg)
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """
        Пополнить баланс.

        Args:
            amount: Сумма пополнения

        Raises:
            ValueError: Если сумма не положительная
        """
        if amount <= 0:
            msg = "Сумма пополнения должна быть положительной"
            raise ValueError(msg)
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        """
        Снять средства.

        Args:
            amount: Сумма снятия

        Raises:
            ValueError: Если сумма не положительная или превышает баланс
        """
        if amount <= 0:
            msg = "Сумма снятия должна быть положительной"
            raise ValueError(msg)
        if amount > self._balance:
            msg = (
                f"Недостаточно средств: доступно {self._balance:.4f} "
                f"{self.currency_code}, требуется {amount:.4f} "
                f"{self.currency_code}"
            )
            raise ValueError(msg)
        self._balance -= amount

    def get_balance_info(self) -> dict:
        """
        Получить информацию о балансе.

        Returns:
            Словарь с информацией о кошельке
        """
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    def to_dict(self) -> dict:
        """Конвертировать кошелек в словарь для сохранения."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }


class Portfolio:
    """Класс портфеля пользователя."""

    def __init__(self, user_id: int, wallets: Optional[dict] = None):
        """
        Инициализация портфеля.

        Args:
            user_id: ID пользователя
            wallets: Словарь кошельков (опционально)
        """
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = {}

        if wallets:
            for currency_code, wallet_data in wallets.items():
                if isinstance(wallet_data, Wallet):
                    self._wallets[currency_code] = wallet_data
                else:
                    code = wallet_data.get("currency_code", currency_code)
                    bal = wallet_data.get("balance", 0.0)
                    self._wallets[currency_code] = Wallet(
                        currency_code=code,
                        balance=bal,
                    )

    @property
    def user_id(self) -> int:
        """Получить ID пользователя."""
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Получить копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавить новый кошелек.

        Args:
            currency_code: Код валюты

        Returns:
            Созданный кошелек

        Raises:
            ValueError: Если кошелек уже существует
        """
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            msg = f"Кошелек {currency_code} уже существует"
            raise ValueError(msg)

        wallet = Wallet(currency_code)
        self._wallets[currency_code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """
        Получить кошелек по коду валюты.

        Args:
            currency_code: Код валюты

        Returns:
            Кошелек или None если не найден
        """
        return self._wallets.get(currency_code.upper())

    def get_or_create_wallet(self, currency_code: str) -> Wallet:
        """
        Получить существующий или создать новый кошелек.

        Args:
            currency_code: Код валюты

        Returns:
            Кошелек
        """
        currency_code = currency_code.upper()
        if currency_code not in self._wallets:
            return self.add_currency(currency_code)
        return self._wallets[currency_code]

    def get_total_value(
        self,
        base_currency: str = "USD",
        exchange_rates: Optional[dict] = None,
    ) -> float:
        """
        Получить общую стоимость портфеля в базовой валюте.

        Args:
            base_currency: Базовая валюта для конвертации
            exchange_rates: Словарь курсов валют

        Returns:
            Общая стоимость в базовой валюте
        """
        if exchange_rates is None:
            exchange_rates = {}

        total = 0.0
        base_currency = base_currency.upper()

        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total += wallet.balance
            else:
                # Ищем курс currency -> base
                rate_key = f"{currency_code}_{base_currency}"
                if rate_key in exchange_rates:
                    rate = exchange_rates[rate_key].get("rate", 0)
                    total += wallet.balance * rate
                # Если курс не найден, пропускаем валюту

        return total

    def to_dict(self) -> dict:
        """Конвертировать портфель в словарь для сохранения."""
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()

        return {"user_id": self._user_id, "wallets": wallets_dict}
