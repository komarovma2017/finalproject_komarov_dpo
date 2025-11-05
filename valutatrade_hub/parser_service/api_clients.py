"""API клиенты для получения курсов валют."""

import logging
from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Базовый класс для API клиентов."""

    def __init__(self, config: ParserConfig):
        """
        Инициализация клиента.

        Args:
            config: Конфигурация парсера
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fetch_rates(self) -> dict:
        """
        Получить курсы валют.

        Returns:
            Словарь с курсами в формате {pair_key: rate}

        Raises:
            ApiRequestError: При ошибке обращения к API
        """


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API (криптовалюты)."""

    def fetch_rates(self) -> dict:
        """Получить курсы криптовалют."""
        try:
            # Формируем список ID для запроса
            ids = [
                self.config.CRYPTO_ID_MAP.get(code)
                for code in self.config.CRYPTO_CURRENCIES
            ]
            ids_str = ",".join(ids)

            # Формируем URL
            url = self.config.COINGECKO_URL
            params = {
                "ids": ids_str,
                "vs_currencies": self.config.BASE_CURRENCY.lower()
            }

            # Выполняем запрос
            self.logger.info(f"Fetching from CoinGecko: {url}")
            response = requests.get(
                url,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )

            # Проверяем статус
            if response.status_code != 200:
                raise ApiRequestError(
                    f"CoinGecko returned status {response.status_code}"
                )

            data = response.json()

            # Преобразуем в стандартный формат
            rates = {}
            for code in self.config.CRYPTO_CURRENCIES:
                crypto_id = self.config.CRYPTO_ID_MAP.get(code)
                if crypto_id in data:
                    base_lower = self.config.BASE_CURRENCY.lower()
                    if base_lower in data[crypto_id]:
                        rate = data[crypto_id][base_lower]
                        pair_key = f"{code}_{self.config.BASE_CURRENCY}"
                        rates[pair_key] = rate

            self.logger.info(f"CoinGecko: fetched {len(rates)} rates")
            return rates

        except requests.exceptions.Timeout:
            raise ApiRequestError("CoinGecko request timeout")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("CoinGecko connection error")
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko error: {e}")
        except Exception as e:
            raise ApiRequestError(f"CoinGecko unexpected error: {e}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API (фиатные валюты)."""

    def fetch_rates(self) -> dict:
        """Получить курсы фиатных валют."""
        try:
            # Формируем URL с API ключом
            url = (
                f"{self.config.EXCHANGERATE_API_URL}/"
                f"{self.config.EXCHANGERATE_API_KEY}/"
                f"latest/{self.config.BASE_CURRENCY}"
            )

            # Выполняем запрос
            self.logger.info("Fetching from ExchangeRate-API")
            response = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT
            )

            # Проверяем статус
            if response.status_code == 401:
                raise ApiRequestError(
                    "ExchangeRate-API: Invalid API key"
                )
            elif response.status_code == 429:
                raise ApiRequestError(
                    "ExchangeRate-API: Rate limit exceeded"
                )
            elif response.status_code != 200:
                raise ApiRequestError(
                    f"ExchangeRate-API returned status "
                    f"{response.status_code}"
                )

            data = response.json()

            # Проверяем результат
            if data.get("result") != "success":
                raise ApiRequestError(
                    f"ExchangeRate-API error: {data.get('error-type')}"
                )

            # Преобразуем в стандартный формат
            rates_data = data.get("rates", {})
            rates = {}

            for code in self.config.FIAT_CURRENCIES:
                if code in rates_data:
                    # Курс дан как FROM_BASE_TO_CODE
                    # Нам нужно FROM_CODE_TO_BASE
                    rate_from_base = rates_data[code]
                    if rate_from_base != 0:
                        rate_to_base = 1.0 / rate_from_base
                        pair_key = f"{code}_{self.config.BASE_CURRENCY}"
                        rates[pair_key] = rate_to_base

            self.logger.info(
                f"ExchangeRate-API: fetched {len(rates)} rates"
            )
            return rates

        except requests.exceptions.Timeout:
            raise ApiRequestError("ExchangeRate-API request timeout")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("ExchangeRate-API connection error")
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API error: {e}")
        except ApiRequestError:
            raise
        except Exception as e:
            raise ApiRequestError(
                f"ExchangeRate-API unexpected error: {e}"
            )

