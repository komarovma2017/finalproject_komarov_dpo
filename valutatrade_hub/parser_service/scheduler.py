"""Планировщик периодического обновления курсов."""

import logging
import time

from valutatrade_hub.parser_service.updater import RatesUpdater


class RatesScheduler:
    """Планировщик автоматического обновления курсов."""

    def __init__(self, interval_seconds: int = 300):
        """
        Инициализация планировщика.

        Args:
            interval_seconds: Интервал обновления в секундах
        """
        self.interval_seconds = interval_seconds
        self.updater = RatesUpdater()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running = False

    def start(self):
        """Запустить планировщик."""
        self.running = True
        self.logger.info(
            f"Scheduler started with interval {self.interval_seconds}s"
        )

        while self.running:
            try:
                self.logger.info("Scheduled update triggered")
                self.updater.run_update()
                self.logger.info("Scheduled update completed")
            except Exception as e:
                self.logger.error(f"Scheduled update failed: {e}")

            # Ждем до следующего обновления
            time.sleep(self.interval_seconds)

    def stop(self):
        """Остановить планировщик."""
        self.running = False
        self.logger.info("Scheduler stopped")

