import configparser
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from logger import Logger

SHOW_LOG = True


class DataPreprocessor:
    """Класс для загрузки, разделения и масштабирования данных."""

    def __init__(self) -> None:
        """Инициализация препроцессора с конфигурацией из config.ini."""
        logger = Logger(SHOW_LOG)
        self.log = logger.get_logger(__name__)
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.log.info("DataPreprocessor инициализирован")

    async def prepare_data(self, X_raw: list, y_raw: list) -> tuple:
        """Разделение и масштабирование данных."""
        columns = ["RI", "Na", "Mg", "Al", "Si", "K", "Ca", "Ba", "Fe"]
        X = pd.DataFrame(X_raw, columns=columns)
        y = pd.Series(y_raw, name="Type")

        self.log.info(f"Данные загружены: X.shape={X.shape}, y.shape={y.shape}")

        test_size = self.config.getfloat("MODEL", "test_size")
        random_state = self.config.getint("MODEL", "random_state")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size,
            random_state=random_state, stratify=y
        )
        self.log.info(f"Данные разделены: train={X_train.shape}, test={X_test.shape}")

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        X_train_scaled = pd.DataFrame(X_train_scaled, columns=columns)
        X_test_scaled = pd.DataFrame(X_test_scaled, columns=columns)

        self.log.info("Данные отмасштабированы (StandardScaler)")
        return X_train_scaled, X_test_scaled, y_train, y_test