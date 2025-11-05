"""CLI интерфейс для взаимодействия с пользователем."""

from __future__ import annotations

import sys

from valutatrade_hub.core.currencies import get_all_currencies, get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import User
from valutatrade_hub.core.usecases import (
    PortfolioService,
    RateService,
    UserService,
)
from valutatrade_hub.core.utils import calculate_conversion
from valutatrade_hub.infra.database import DatabaseManager


class CLI:
    """Класс командного интерфейса."""

    def __init__(self):
        """Инициализация CLI."""
        self.user_service = UserService()
        self.portfolio_service = PortfolioService()
        self.rate_service = RateService()
        self.current_user: User | None = None

    def parse_args(self, args: list) -> dict:
        """
        Парсинг аргументов командной строки.

        Args:
            args: Список аргументов

        Returns:
            Словарь с командой и параметрами
        """
        if not args:
            return {"command": "help"}

        command = args[0]
        params = {}

        i = 1
        while i < len(args):
            if args[i].startswith("--"):
                key = args[i][2:]
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    params[key] = args[i + 1]
                    i += 2
                else:
                    params[key] = True
                    i += 1
            else:
                i += 1

        return {"command": command, "params": params}

    def run(self, args: list):
        """
        Выполнить команду.

        Args:
            args: Аргументы командной строки
        """
        parsed = self.parse_args(args)
        command = parsed["command"]
        params = parsed["params"]

        try:
            if command == "register":
                self.cmd_register(params)
            elif command == "login":
                self.cmd_login(params)
            elif command == "show-portfolio":
                self.cmd_show_portfolio(params)
            elif command == "buy":
                self.cmd_buy(params)
            elif command == "sell":
                self.cmd_sell(params)
            elif command == "get-rate":
                self.cmd_get_rate(params)
            elif command == "update-rates":
                self.cmd_update_rates(params)
            elif command == "show-rates":
                self.cmd_show_rates(params)
            elif command == "help":
                self.cmd_help()
            else:
                print(f"Неизвестная команда: {command}")
                print("Используйте 'help' для списка команд")

        except CurrencyNotFoundError as e:
            print(f"❌ {e}")
            print(
                "Поддерживаемые валюты: "
                f"{', '.join(get_all_currencies().keys())}"
            )
        except InsufficientFundsError as e:
            print(f"❌ {e}")
        except ApiRequestError as e:
            print(f"❌ {e}")
        except ValueError as e:
            print(f"❌ {e}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def cmd_register(self, params: dict):
        """Команда регистрации."""
        username = params.get("username")
        password = params.get("password")

        if not username or not password:
            print("❌ Необходимо указать --username и --password")
            return

        try:
            user = self.user_service.register(
                username=username, password=password
            )
            print(
                f"✓ Пользователь '{username}' зарегистрирован "
                f"(id={user.user_id}). "
                f"Войдите: login --username {username} --password ****"
            )
        except ValueError as e:
            if "уже занято" in str(e):
                print(f"❌ Имя пользователя '{username}' уже занято")
            elif "короче 4" in str(e):
                print("❌ Пароль должен быть не короче 4 символов")
            else:
                raise

    def cmd_login(self, params: dict):
        """Команда входа."""
        username = params.get("username")
        password = params.get("password")

        if not username or not password:
            print("❌ Необходимо указать --username и --password")
            return

        try:
            user = self.user_service.login(
                username=username, password=password
            )
            self.current_user = user
            print(f"✓ Вы вошли как '{username}'")
        except ValueError as e:
            if "не найден" in str(e):
                print(f"❌ Пользователь '{username}' не найден")
            elif "Неверный пароль" in str(e):
                print("❌ Неверный пароль")
            else:
                raise

    def cmd_show_portfolio(self, params: dict):
        """Команда показа портфеля."""
        if not self.current_user:
            print("❌ Сначала выполните login")
            return

        base = params.get("base", "USD").upper()

        try:
            # Проверяем базовую валюту
            get_currency(base)

            portfolio = self.portfolio_service.get_portfolio(
                self.current_user.user_id
            )
            if not portfolio or not portfolio.wallets:
                print("Ваш портфель пуст")
                return

            # Получаем курсы
            db = DatabaseManager()
            rates_cache = db.read_rates()

            print(
                f"\nПортфель пользователя '{self.current_user.username}' "
                f"(база: {base}):"
            )

            total = 0.0
            for code, wallet in sorted(portfolio.wallets.items()):
                balance = wallet.balance
                value_in_base = calculate_conversion(
                    balance, code, base, rates_cache
                )

                if value_in_base is not None:
                    total += value_in_base
                    print(
                        f"- {code}: {balance:.4f}  → "
                        f"{value_in_base:.2f} {base}"
                    )
                else:
                    print(f"- {code}: {balance:.4f}  → [курс недоступен]")

            print("-" * 40)
            print(f"ИТОГО: {total:,.2f} {base}")

        except CurrencyNotFoundError:
            print(f"❌ Неизвестная базовая валюта '{base}'")

    def cmd_buy(self, params: dict):
        """Команда покупки валюты."""
        if not self.current_user:
            print("❌ Сначала выполните login")
            return

        currency = params.get("currency")
        amount_str = params.get("amount")

        if not currency or not amount_str:
            print("❌ Необходимо указать --currency и --amount")
            return

        try:
            amount = float(amount_str)
        except ValueError:
            print("❌ 'amount' должен быть числом")
            return

        result = self.portfolio_service.buy(
            user_id=self.current_user.user_id,
            currency_code=currency,
            amount=amount
        )

        rate = result.get("rate")
        if rate:
            print(
                f"✓ Покупка выполнена: {amount:.4f} {result['currency']} "
                f"по курсу {rate:.2f} USD/{result['currency']}"
            )
        else:
            print(
                f"✓ Покупка выполнена: {amount:.4f} {result['currency']}"
            )

        print("Изменения в портфеле:")
        print(
            f"- {result['currency']}: было {result['old_balance']:.4f} → "
            f"стало {result['new_balance']:.4f}"
        )

        if result.get("estimated_cost"):
            print(
                f"Оценочная стоимость покупки: "
                f"{result['estimated_cost']:,.2f} USD"
            )

    def cmd_sell(self, params: dict):
        """Команда продажи валюты."""
        if not self.current_user:
            print("❌ Сначала выполните login")
            return

        currency = params.get("currency")
        amount_str = params.get("amount")

        if not currency or not amount_str:
            print("❌ Необходимо указать --currency и --amount")
            return

        try:
            amount = float(amount_str)
        except ValueError:
            print("❌ 'amount' должен быть числом")
            return

        result = self.portfolio_service.sell(
            user_id=self.current_user.user_id,
            currency_code=currency,
            amount=amount
        )

        rate = result.get("rate")
        if rate:
            print(
                f"✓ Продажа выполнена: {amount:.4f} {result['currency']} "
                f"по курсу {rate:.2f} USD/{result['currency']}"
            )
        else:
            print(
                f"✓ Продажа выполнена: {amount:.4f} {result['currency']}"
            )

        print("Изменения в портфеле:")
        print(
            f"- {result['currency']}: было {result['old_balance']:.4f} → "
            f"стало {result['new_balance']:.4f}"
        )

        if result.get("estimated_revenue"):
            print(
                f"Оценочная выручка: "
                f"{result['estimated_revenue']:,.2f} USD"
            )

    def cmd_get_rate(self, params: dict):
        """Команда получения курса."""
        from_code = params.get("from")
        to_code = params.get("to")

        if not from_code or not to_code:
            print("❌ Необходимо указать --from и --to")
            return

        result = self.rate_service.get_rate(from_code, to_code)

        print(
            f"Курс {result['from']}→{result['to']}: {result['rate']:.8f} "
            f"(обновлено: {result['updated_at']})"
        )
        if result.get("reverse_rate"):
            print(
                f"Обратный курс {result['to']}→{result['from']}: "
                f"{result['reverse_rate']:.8f}"
            )

    def cmd_update_rates(self, params: dict):
        """Команда обновления курсов."""
        source = params.get("source")

        # Импортируем здесь, чтобы избежать циклических импортов
        try:
            from valutatrade_hub.parser_service.updater import RatesUpdater

            print("INFO: Starting rates update...")
            updater = RatesUpdater()
            result = updater.run_update(source_filter=source)

            print(
                f"✓ Update successful. Total rates updated: "
                f"{result['total_updated']}. "
                f"Last refresh: {result['last_refresh']}"
            )

        except Exception as e:
            print(f"❌ Update failed: {e}")
            print("Check logs/parser.log for details.")

    def cmd_show_rates(self, params: dict):
        """Команда показа курсов из кеша."""
        currency = params.get("currency")
        top = params.get("top")
        base = params.get("base", "USD").upper()

        db = DatabaseManager()
        rates_cache = db.read_rates()
        pairs = rates_cache.get("pairs", {})
        last_refresh = rates_cache.get("last_refresh", "неизвестно")

        if not pairs:
            print(
                "Локальный кеш курсов пуст. "
                "Выполните 'update-rates', чтобы загрузить данные."
            )
            return

        print(f"Rates from cache (updated at {last_refresh}):")

        # Фильтрация
        filtered_pairs = {}
        for pair_key, pair_data in pairs.items():
            from_curr, to_curr = pair_key.split("_")

            if currency and currency.upper() != from_curr:
                continue

            if to_curr == base:
                filtered_pairs[pair_key] = pair_data

        if not filtered_pairs:
            if currency:
                print(f"Курс для '{currency}' не найден в кеше.")
            return

        # Сортировка и ограничение
        sorted_pairs = sorted(filtered_pairs.items(), key=lambda x: x[0])

        if top:
            try:
                sorted_pairs = sorted_pairs[:int(top)]
            except ValueError:
                pass

        for pair_key, pair_data in sorted_pairs:
            rate = pair_data.get("rate", 0)
            print(f"- {pair_key}: {rate}")

    def cmd_help(self):
        """Команда помощи."""
        help_text = """
ValutaTrade Hub - Платформа для торговли валютами

Команды:
  register --username <name> --password <pass>
      Регистрация нового пользователя

  login --username <name> --password <pass>
      Вход в систему

  show-portfolio [--base <currency>]
      Показать портфель (по умолчанию база: USD)

  buy --currency <code> --amount <number>
      Купить валюту

  sell --currency <code> --amount <number>
      Продать валюту

  get-rate --from <code> --to <code>
      Получить курс валюты

  update-rates [--source <coingecko|exchangerate>]
      Обновить курсы валют из внешних API

  show-rates [--currency <code>] [--top <N>] [--base <code>]
      Показать курсы из локального кеша

  help
      Показать эту справку

Поддерживаемые валюты: BTC, ETH, SOL, USD, EUR, GBP, RUB
"""
        print(help_text)


def main():
    """Точка входа в CLI."""
    cli = CLI()
    cli.run(sys.argv[1:])

