import configparser
import os
import traceback
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
        self.project_path = os.path.join(os.getcwd(), "data")
        os.makedirs(self.project_path, exist_ok=True)

        self.X_train_path = os.path.join(self.project_path, "X_train.csv")
        self.y_train_path = os.path.join(self.project_path, "y_train.csv")
        self.X_test_path = os.path.join(self.project_path, "X_test.csv")
        self.y_test_path = os.path.join(self.project_path, "y_test.csv")

        self.log.info("DataPreprocessor инициализирован")

    async def prepare_data(self, X_raw: list, y_raw: list) -> tuple:
        """
        Полный пайплайн предобработки: разделение, масштабирование, сохранение.

        Args:
            X_raw: список списков признаков из БД.
            y_raw: список меток классов из БД.

        Returns:
            tuple: (X_train_scaled, X_test_scaled, y_train, y_test)
        """
        # Конвертация в DataFrame (аналогично загрузке CSV)
        columns = ["RI", "Na", "Mg", "Al", "Si", "K", "Ca", "Ba", "Fe"]
        X = pd.DataFrame(X_raw, columns=columns)
        y = pd.Series(y_raw, name="Type")

        self.log.info(f"Данные загружены: X.shape={X.shape}, y.shape={y.shape}")

        # Разделение на train/test
        test_size = self.config.getfloat("MODEL", "test_size")
        random_state = self.config.getint("MODEL", "random_state")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size,
            random_state=random_state, stratify=y
        )
        self.log.info(
            f"Данные разделены: train={X_train.shape}, test={X_test.shape}"
        )

        # Масштабирование
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Конвертация обратно в DataFrame с сохранением колонок
        X_train_scaled = pd.DataFrame(X_train_scaled, columns=columns)
        X_test_scaled = pd.DataFrame(X_test_scaled, columns=columns)

        self.log.info("Данные отмасштабированы (StandardScaler)")

        # Сохранение разделённых данных
        self._save_data(X_train_scaled, self.X_train_path)
        self._save_data(y_train.to_frame(), self.y_train_path)
        self._save_data(X_test_scaled, self.X_test_path)
        self._save_data(y_test.to_frame(), self.y_test_path)

        self.log.info("Предобработка завершена")
        return X_train_scaled, X_test_scaled, y_train, y_test

    def _save_data(self, data: pd.DataFrame, path: str) -> bool:
        """
        Сохранение данных в CSV.

        Args:
            data: DataFrame для сохранения.
            path: путь к файлу.

        Returns:
            bool: True если сохранение успешно.
        """
        try:
            data.to_csv(path, index=True)
            self.log.info(f"Данные сохранены: {path}")
            return os.path.isfile(path)
        except Exception:
            self.log.error(traceback.format_exc())
            return False