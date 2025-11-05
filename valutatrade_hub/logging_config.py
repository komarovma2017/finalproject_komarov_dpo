"""Конфигурация логирования для приложения."""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str = "logs/actions.log", level: int = logging.INFO):
    """
    Настройка логирования с ротацией файлов.

    Args:
        log_file: Путь к файлу логов
        level: Уровень логирования
    """
    # Создаем директорию для логов, если её нет
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Формат логов: timestamp, уровень, сообщение
    log_format = (
        "%(levelname)s %(asctime)s %(message)s"
    )
    date_format = "%Y-%m-%dT%H:%M:%S"

    # Создаем форматтер
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Настраиваем root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Очищаем существующие handlers
    logger.handlers.clear()

    # Handler для файла с ротацией (макс 10 MB, 5 backup файлов)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

