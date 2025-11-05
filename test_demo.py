"""Демонстрационный тест работы приложения."""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

from valutatrade_hub.cli.interface import CLI
from valutatrade_hub.logging_config import setup_logging


def test_demo():
    """Тестирование основного потока работы."""
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ ValutaTrade Hub")
    print("=" * 60)

    # Настраиваем логирование
    setup_logging()

    cli = CLI()

    print("\n1. Регистрация пользователя alice...")
    try:
        cli.run(["register", "--username", "alice", "--password", "1234"])
    except Exception as e:
        print(f"Ошибка при регистрации: {e}")

    print("\n2. Вход в систему как alice...")
    try:
        cli.run(["login", "--username", "alice", "--password", "1234"])
    except Exception as e:
        print(f"Ошибка при входе: {e}")

    print("\n3. Покупка 0.05 BTC...")
    try:
        cli.run(["buy", "--currency", "BTC", "--amount", "0.05"])
    except Exception as e:
        print(f"Ошибка при покупке: {e}")

    print("\n4. Покупка 100 EUR...")
    try:
        cli.run(["buy", "--currency", "EUR", "--amount", "100"])
    except Exception as e:
        print(f"Ошибка при покупке: {e}")

    print("\n5. Просмотр портфеля...")
    try:
        cli.run(["show-portfolio"])
    except Exception as e:
        print(f"Ошибка при просмотре портфеля: {e}")

    print("\n6. Продажа 0.02 BTC...")
    try:
        cli.run(["sell", "--currency", "BTC", "--amount", "0.02"])
    except Exception as e:
        print(f"Ошибка при продаже: {e}")

    print("\n7. Просмотр обновленного портфеля...")
    try:
        cli.run(["show-portfolio"])
    except Exception as e:
        print(f"Ошибка при просмотре портфеля: {e}")

    print("\n8. Попытка получить курс (может не работать без update-rates)...")
    try:
        cli.run(["get-rate", "--from", "BTC", "--to", "USD"])
    except Exception as e:
        print(f"Ожидаемо: {e}")

    print("\n9. Справка...")
    try:
        cli.run(["help"])
    except Exception as e:
        print(f"Ошибка: {e}")

    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)
    print("\nПроверьте файлы в директории data/:")
    print("- data/users.json")
    print("- data/portfolios.json")
    print("\nИ логи в директории logs/:")
    print("- logs/actions.log")


if __name__ == "__main__":
    test_demo()

