"""Командный интерфейс приложения."""

import argparse
import sys

from valutatrade_hub.core.usecases import (
    AuthService,
    PortfolioService,
    RateService,
)
from valutatrade_hub.core.utils import DataStorage


class CLI:
    """Класс командного интерфейса."""

    def __init__(self):
        """Инициализация CLI."""
        self.storage = DataStorage()
        self.auth_service = AuthService(self.storage)
        self.portfolio_service = PortfolioService(
            self.storage, self.auth_service
        )
        self.rate_service = RateService(self.storage)

    def run(self, args: list[str] | None = None) -> None:
        """
        Запустить CLI.

        Args:
            args: Аргументы командной строки
        """
        parser = argparse.ArgumentParser(
            description="ValutaTrade Hub - Платформа торговли валютами",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        subparsers = parser.add_subparsers(
            dest="command", help="Доступные команды"
        )

        # Команда register
        register_parser = subparsers.add_parser(
            "register", help="Регистрация нового пользователя"
        )
        register_parser.add_argument(
            "--username", required=True, help="Имя пользователя"
        )
        register_parser.add_argument(
            "--password", required=True, help="Пароль"
        )

        # Команда login
        login_parser = subparsers.add_parser("login", help="Вход в систему")
        login_parser.add_argument(
            "--username", required=True, help="Имя пользователя"
        )
        login_parser.add_argument("--password", required=True, help="Пароль")

        # Команда logout
        subparsers.add_parser("logout", help="Выход из системы")

        # Команда show-portfolio
        portfolio_parser = subparsers.add_parser(
            "show-portfolio", help="Показать портфель"
        )
        portfolio_parser.add_argument(
            "--base", default="USD", help="Базовая валюта (по умолчанию USD)"
        )

        # Команда buy
        buy_parser = subparsers.add_parser("buy", help="Купить валюту")
        buy_parser.add_argument(
            "--currency", required=True, help="Код валюты"
        )
        buy_parser.add_argument(
            "--amount", required=True, type=float, help="Количество"
        )

        # Команда sell
        sell_parser = subparsers.add_parser("sell", help="Продать валюту")
        sell_parser.add_argument(
            "--currency", required=True, help="Код валюты"
        )
        sell_parser.add_argument(
            "--amount", required=True, type=float, help="Количество"
        )

        # Команда get-rate
        rate_parser = subparsers.add_parser(
            "get-rate", help="Получить курс валют"
        )
        rate_parser.add_argument(
            "--from", dest="from_currency", required=True, help="Исходная валюта"
        )
        rate_parser.add_argument(
            "--to", dest="to_currency", required=True, help="Целевая валюта"
        )

        # Парсинг аргументов
        if args is None:
            args = sys.argv[1:]

        parsed_args = parser.parse_args(args)

        if not parsed_args.command:
            parser.print_help()
            return

        # Выполнение команды
        self._execute_command(parsed_args)

    def _execute_command(self, args: argparse.Namespace) -> None:
        """
        Выполнить команду.

        Args:
            args: Распарсенные аргументы
        """
        command = args.command

        if command == "register":
            self._cmd_register(args.username, args.password)
        elif command == "login":
            self._cmd_login(args.username, args.password)
        elif command == "logout":
            self._cmd_logout()
        elif command == "show-portfolio":
            self._cmd_show_portfolio(args.base)
        elif command == "buy":
            self._cmd_buy(args.currency, args.amount)
        elif command == "sell":
            self._cmd_sell(args.currency, args.amount)
        elif command == "get-rate":
            self._cmd_get_rate(args.from_currency, args.to_currency)

    def _cmd_register(self, username: str, password: str) -> None:
        """
        Команда регистрации.

        Args:
            username: Имя пользователя
            password: Пароль
        """
        success, message, _ = self.auth_service.register_user(
            username, password
        )
        print(message)
        if not success:
            sys.exit(1)

    def _cmd_login(self, username: str, password: str) -> None:
        """
        Команда входа.

        Args:
            username: Имя пользователя
            password: Пароль
        """
        success, message = self.auth_service.login_user(username, password)
        print(message)
        if not success:
            sys.exit(1)

    def _cmd_logout(self) -> None:
        """Команда выхода."""
        if not self.auth_service.is_logged_in():
            print("Вы не авторизованы")
            return

        user = self.auth_service.get_current_user()
        self.auth_service.logout()
        print(f"Вы вышли из системы (пользователь '{user.username}')")

    def _cmd_show_portfolio(self, base: str) -> None:
        """
        Команда показа портфеля.

        Args:
            base: Базовая валюта
        """
        success, message = self.portfolio_service.show_portfolio(base)
        print(message)
        if not success:
            sys.exit(1)

    def _cmd_buy(self, currency: str, amount: float) -> None:
        """
        Команда покупки валюты.

        Args:
            currency: Код валюты
            amount: Количество
        """
        success, message = self.portfolio_service.buy_currency(
            currency, amount
        )
        print(message)
        if not success:
            sys.exit(1)

    def _cmd_sell(self, currency: str, amount: float) -> None:
        """
        Команда продажи валюты.

        Args:
            currency: Код валюты
            amount: Количество
        """
        success, message = self.portfolio_service.sell_currency(
            currency, amount
        )
        print(message)
        if not success:
            sys.exit(1)

    def _cmd_get_rate(self, from_currency: str, to_currency: str) -> None:
        """
        Команда получения курса.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
        """
        success, message = self.rate_service.get_rate(
            from_currency, to_currency
        )
        print(message)
        if not success:
            sys.exit(1)


def main() -> None:
    """Точка входа в CLI."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
