import logging
import os
import sys

FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s — %(message)s")
LOG_FILE = os.path.join(os.getcwd(), "logfile.log")


class Logger:
    """
    Класс для логирования поведения компонентов системы.
    """

    def __init__(self, show: bool) -> None:
        """
        Инициализация логгера.

        Args:
            show (bool): если True, все логи выводятся в терминал.
        """
        self.show = show

    def get_console_handler(self) -> logging.StreamHandler:
        """Получение обработчика для вывода в консоль."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(FORMATTER)
        return console_handler

    def get_file_handler(self) -> logging.FileHandler:
        """Получение обработчика для записи в файл."""
        file_handler = logging.FileHandler(LOG_FILE, mode='w')
        file_handler.setFormatter(FORMATTER)
        return file_handler

    def get_logger(self, logger_name: str):
        """
        Создание и настройка логгера.

        Args:
            logger_name (str): имя логгера.

        Returns:
            logging.Logger: настроенный объект логгера.
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        if self.show:
            logger.addHandler(self.get_console_handler())
        logger.addHandler(self.get_file_handler())
        logger.propagate = False
        return logger