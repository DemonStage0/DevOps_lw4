import os
import pickle
import pandas as pd
from sklearn.preprocessing import StandardScaler
from logger import Logger

SHOW_LOG = True


class Predictor:
    """Класс для загрузки модели и выполнения предсказаний."""

    def __init__(self) -> None:
        """Инициализация предиктора."""
        logger = Logger(SHOW_LOG)
        self.log = logger.get_logger(__name__)
        self.log.info("Predictor инициализирован")

    def load_latest_model(self):
        """
        Загрузка последней сохранённой модели.

        Returns:
            model: обученная модель или None.
        """
        exp_root = "experiments"
        if not os.path.exists(exp_root):
            return None
        exps = sorted(
            [d for d in os.listdir(exp_root) if d.startswith("exp_")],
            key=lambda x: int(x.split("_")[1]),
        )
        if not exps:
            return None
        latest = os.path.join(exp_root, exps[-1], "trained_model.pkl")
        with open(latest, "rb") as f:
            model = pickle.load(f)
        return model

    def predict(self, features: list) -> int:
        """
        Предсказание класса по вектору признаков.

        Args:
            features: список из 9 признаков [RI, Na, Mg, Al, Si, K, Ca, Ba, Fe].

        Returns:
            int: предсказанный класс (1-7).
        """
        model = self.load_latest_model()
        if model is None:
            raise FileNotFoundError("Нет предобученной модели")

        # Конвертируем в DataFrame с правильными именами колонок
        columns = ["RI", "Na", "Mg", "Al", "Si", "K", "Ca", "Ba", "Fe"]
        X = pd.DataFrame([features], columns=columns)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        return int(model.predict(X_scaled)[0])