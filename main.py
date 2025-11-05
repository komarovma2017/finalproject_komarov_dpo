"""Точка входа в приложение ValutaTrade Hub."""


from valutatrade_hub.cli.interface import main as cli_main
from valutatrade_hub.logging_config import setup_logging


def main():
    """Главная функция приложения."""
    # Настраиваем логирование
    setup_logging()

    # Запускаем CLI
    cli_main()


if __name__ == "__main__":
    main()

