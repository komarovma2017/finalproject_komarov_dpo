"""Вспомогательные функции для работы с данными."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class DataStorage:
    """Класс для работы с JSON хранилищем."""

    def __init__(self, data_dir: str = "data"):
        """
        Инициализация хранилища.

        Args:
            data_dir: Директория с данными
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.users_file = self.data_dir / "users.json"
        self.portfolios_file = self.data_dir / "portfolios.json"
        self.rates_file = self.data_dir / "rates.json"

        # Создаем файлы если они не существуют
        self._init_file(self.users_file, [])
        self._init_file(self.portfolios_file, [])
        self._init_file(
            self.rates_file,
            {
                "EUR_USD": {
                    "rate": 1.0786,
                    "updated_at": datetime.now().isoformat(),
                },
                "BTC_USD": {
                    "rate": 59337.21,
                    "updated_at": datetime.now().isoformat(),
                },
                "RUB_USD": {
                    "rate": 0.01016,
                    "updated_at": datetime.now().isoformat(),
                },
                "ETH_USD": {
                    "rate": 3720.00,
                    "updated_at": datetime.now().isoformat(),
                },
                "source": "default",
                "last_refresh": datetime.now().isoformat(),
            },
        )

    def _init_file(self, file_path: Path, default_data: Any) -> None:
        """
        Инициализировать файл данными по умолчанию если не существует.

        Args:
            file_path: Путь к файлу
            default_data: Данные по умолчанию
        """
        if not file_path.exists():
            self._write_json(file_path, default_data)

    def _read_json(self, file_path: Path) -> Any:
        """
        Прочитать JSON файл.

        Args:
            file_path: Путь к файлу

        Returns:
            Данные из файла
        """
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            is_list_file = "users" in str(file_path) or "portfolios" in str(
                file_path
            )
            return [] if is_list_file else {}

    def _write_json(self, file_path: Path, data: Any) -> None:
        """
        Записать данные в JSON файл.

        Args:
            file_path: Путь к файлу
            data: Данные для записи
        """
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_users(self) -> list:
        """Загрузить всех пользователей."""
        return self._read_json(self.users_file)

    def save_users(self, users: list) -> None:
        """
        Сохранить пользователей.

        Args:
            users: Список пользователей
        """
        self._write_json(self.users_file, users)

    def load_portfolios(self) -> list:
        """Загрузить все портфели."""
        return self._read_json(self.portfolios_file)

    def save_portfolios(self, portfolios: list) -> None:
        """
        Сохранить портфели.

        Args:
            portfolios: Список портфелей
        """
        self._write_json(self.portfolios_file, portfolios)

    def load_rates(self) -> dict:
        """Загрузить курсы валют."""
        return self._read_json(self.rates_file)

    def save_rates(self, rates: dict) -> None:
        """
        Сохранить курсы валют.

        Args:
            rates: Словарь курсов
        """
        self._write_json(self.rates_file, rates)

    def find_user_by_username(self, username: str) -> Optional[dict]:
        """
        Найти пользователя по имени.

        Args:
            username: Имя пользователя

        Returns:
            Данные пользователя или None
        """
        users = self.load_users()
        for user in users:
            if user["username"] == username:
                return user
        return None

    def find_portfolio_by_user_id(self, user_id: int) -> Optional[dict]:
        """
        Найти портфель по ID пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Данные портфеля или None
        """
        portfolios = self.load_portfolios()
        for portfolio in portfolios:
            if portfolio["user_id"] == user_id:
                return portfolio
        return None

    def get_next_user_id(self) -> int:
        """
        Получить следующий ID пользователя.

        Returns:
            Новый ID
        """
        users = self.load_users()
        if not users:
            return 1
        return max(user["user_id"] for user in users) + 1


def validate_currency_code(currency_code: str) -> str:
    """
    Валидировать код валюты.

    Args:
        currency_code: Код валюты

    Returns:
        Код валюты в верхнем регистре

    Raises:
        ValueError: Если код валюты невалидный
    """
    if not currency_code or not currency_code.strip():
        msg = "Код валюты не может быть пустым"
        raise ValueError(msg)
    return currency_code.strip().upper()


def validate_amount(amount: float) -> float:
    """
    Валидировать сумму.

    Args:
        amount: Сумма

    Returns:
        Валидированная сумма

    Raises:
        ValueError: Если сумма невалидная
    """
    try:
        amount = float(amount)
    except (ValueError, TypeError) as e:
        msg = "'amount' должен быть числом"
        raise ValueError(msg) from e

    if amount <= 0:
        msg = "'amount' должен быть положительным числом"
        raise ValueError(msg)

    return amount


def format_currency(amount: float, currency_code: str) -> str:
    """
    Форматировать сумму с валютой.

    Args:
        amount: Сумма
        currency_code: Код валюты

    Returns:
        Отформатированная строка
    """
    return f"{amount:,.2f} {currency_code}"


def get_rate_key(from_currency: str, to_currency: str) -> str:
    """
    Получить ключ для курса валют.

    Args:
        from_currency: Исходная валюта
        to_currency: Целевая валюта

    Returns:
        Ключ в формате "FROM_TO"
    """
    return f"{from_currency.upper()}_{to_currency.upper()}"
