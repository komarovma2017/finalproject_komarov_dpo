"""Декораторы для логирования операций."""

import functools
import logging
from datetime import datetime


def log_action(action_name: str, verbose: bool = False):
    """
    Декоратор для логирования доменных операций.

    Args:
        action_name: Название операции (BUY, SELL, REGISTER, LOGIN)
        verbose: Флаг для детального логирования

    Декоратор логирует операции на уровне INFO и не глотает исключения.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger()
            timestamp = datetime.now().isoformat()

            # Подготовка контекста логирования
            log_data = {
                "timestamp": timestamp,
                "action": action_name,
            }

            # Извлечение параметров из kwargs
            if "user_id" in kwargs:
                log_data["user_id"] = kwargs["user_id"]
            if "username" in kwargs:
                log_data["username"] = kwargs["username"]
            if "currency_code" in kwargs:
                log_data["currency"] = kwargs["currency_code"]
            if "amount" in kwargs:
                log_data["amount"] = kwargs["amount"]

            try:
                result = func(*args, **kwargs)
                log_data["result"] = "OK"

                # Формирование сообщения
                msg_parts = [action_name]
                if "username" in log_data:
                    msg_parts.append(f"user='{log_data['username']}'")
                if "currency" in log_data:
                    msg_parts.append(f"currency='{log_data['currency']}'")
                if "amount" in log_data:
                    msg_parts.append(f"amount={log_data['amount']}")
                msg_parts.append("result=OK")

                logger.info(" ".join(msg_parts))
                return result

            except Exception as e:
                log_data["result"] = "ERROR"
                log_data["error_type"] = type(e).__name__
                log_data["error_message"] = str(e)

                # Формирование сообщения об ошибке
                msg_parts = [action_name]
                if "username" in log_data:
                    msg_parts.append(f"user='{log_data['username']}'")
                if "currency" in log_data:
                    msg_parts.append(f"currency='{log_data['currency']}'")
                msg_parts.append(
                    f"result=ERROR error={log_data['error_type']}"
                )

                logger.error(" ".join(msg_parts))
                raise

        return wrapper
    return decorator

