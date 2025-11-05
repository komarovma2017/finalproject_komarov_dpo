"""Координатор обновления курсов валют."""

from __future__ import annotations

import logging
from datetime import datetime

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage


class RatesUpdater:
    """Координатор обновления курсов."""

    def __init__(self):
        """Инициализация обновлятора."""
        self.config = ParserConfig()
        self.storage = RatesStorage()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Инициализируем клиенты
        self.clients = {
            "coingecko": CoinGeckoClient(self.config),
            "exchangerate": ExchangeRateApiClient(self.config)
        }

    def run_update(self, source_filter: str | None = None) -> dict:
        """
        Выполнить обновление курсов.

        Args:
            source_filter: Фильтр источника (coingecko или exchangerate)

        Returns:
            Результат обновления
        """
        self.logger.info("Starting rates update")
        all_rates = {}
        errors = []

        # Определяем, какие клиенты использовать
        clients_to_use = self.clients
        if source_filter:
            filter_lower = source_filter.lower()
            if filter_lower in self.clients:
                clients_to_use = {filter_lower: self.clients[filter_lower]}
            else:
                self.logger.warning(f"Unknown source filter: {source_filter}")

        # Опрашиваем каждый клиент
        for name, client in clients_to_use.items():
            try:
                self.logger.info(f"Fetching from {name}...")
                rates = client.fetch_rates()

                if rates:
                    all_rates.update(rates)
                    self.logger.info(
                        f"✓ {name}: fetched {len(rates)} rates"
                    )
                    print(f"INFO: Fetching from {name}... OK ({len(rates)} rates)")
                else:
                    self.logger.warning(f"{name}: no rates returned")

            except ApiRequestError as e:
                error_msg = f"Failed to fetch from {name}: {e}"
                self.logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error from {name}: {e}"
                self.logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                errors.append(error_msg)

        # Сохраняем результаты
        if all_rates:
            timestamp = datetime.now().isoformat()
            self.logger.info(
                f"Writing {len(all_rates)} rates to storage..."
            )
            print(
                f"INFO: Writing {len(all_rates)} rates to data/rates.json..."
            )

            # Сохраняем с источником "ParserService"
            self.storage.save_rates(all_rates, "ParserService")

            return {
                "total_updated": len(all_rates),
                "last_refresh": timestamp,
                "errors": errors
            }
        else:
            raise ApiRequestError(
                "No rates fetched from any source. Check logs."
            )

