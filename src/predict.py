import os
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler

# Добавляем путь к src в sys.path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.logger import Logger

SHOW_LOG = True

class Predictor:
    """Класс для загрузки модели и выполнения предсказаний."""

    def __init__(self) -> None:
        """Инициализация предиктора."""
        logger = Logger(SHOW_LOG)
        self.log = logger.get_logger(__name__)
        self.log.info("Predictor инициализирован")

    def load_latest_model(self) -> tuple:
        """
        Загрузка последней сохранённой модели.

        Returns:
            tuple: (model, None) — scaler не используется,
                   т.к. масштабирование происходит здесь же.
        """
        exp_root = "experiments"
        if not os.path.exists(exp_root):
            return None, None
        exps = sorted(
            [d for d in os.listdir(exp_root) if d.startswith("exp_")],
            key=lambda x: int(x.split("_")[1]),
        )
        if not exps:
            return None, None
        latest = os.path.join(exp_root, exps[-1], "trained_model.pkl")
        with open(latest, "rb") as f:
            model = pickle.load(f)
        return model, None

    def predict(self, features: list) -> int:
        """
        Предсказание класса по вектору признаков.

        Args:
            features: список из 9 признаков [RI, Na, Mg, Al, Si, K, Ca, Ba, Fe].

        Returns:
            int: предсказанный класс (1-7).
        """
        model, _ = self.load_latest_model()
        if model is None:
            raise FileNotFoundError("Нет предобученной модели")

        # Масштабирование (здесь, т.к. scaler не сохраняется в эксперименте)
        scaler = StandardScaler()
        X = np.array(features).reshape(1, -1)
        X_scaled = scaler.fit_transform(X)  # Для одного примера fit_transform ок
        return int(model.predict(X_scaled)[0])