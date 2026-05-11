import configparser
import os
import sys
import unittest
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from train import ModelTrainer
from preprocess import DataPreprocessor

config = configparser.ConfigParser()
config.read(os.path.join(os.getcwd(), "config.ini"))


class TestModelTrainer(unittest.TestCase):
    """Тестирование класса ModelTrainer."""

    def setUp(self) -> None:
        """Инициализация перед каждым тестом."""
        self.trainer = ModelTrainer()

    def test_init(self):
        """Проверка инициализации."""
        self.assertIsNotNone(self.trainer.config)
        self.assertTrue(os.path.exists("config.ini"))

    def test_train(self):
        """Проверка обучения модели."""
        async def run():
            from sklearn.datasets import make_classification

            X, y = make_classification(
                n_samples=100, n_features=9, n_classes=7,
                n_informative=7, n_redundant=0, random_state=42
            )
            preprocessor = DataPreprocessor()
            X_tr, X_te, y_tr, y_te = await preprocessor.prepare_data(
                X.tolist(), y.tolist()
            )
            return await self.trainer.train(X_tr, X_te, y_tr, y_te)

        result = asyncio.run(run())
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['f1_score'], 0.0)


if __name__ == "__main__":
    unittest.main()