import os
import sys
import unittest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestAPI(unittest.TestCase):
    """Тестирование API эндпоинтов."""

    BASE_URL = "http://localhost:8000"

    def test_health_check(self):
        """Проверка доступности API."""
        try:
            resp = requests.get(f"{self.BASE_URL}/")
            self.assertEqual(resp.status_code, 200)
        except requests.ConnectionError:
            self.skipTest("API не запущен")

    def test_train(self):
        """Проверка эндпоинта обучения."""
        try:
            resp = requests.get(f"{self.BASE_URL}/train")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("message", data)
        except requests.ConnectionError:
            self.skipTest("API не запущен")

    def test_predict(self):
        """Проверка эндпоинта предсказания."""
        try:
            # Сначала обучаем модель
            requests.get(f"{self.BASE_URL}/train")
            # Затем предсказываем
            params = {
                "RI": 1.52101, "Na": 13.64, "Mg": 4.49,
                "Al": 1.1, "Si": 71.78, "K": 0.06,
                "Ca": 8.75, "Ba": 0.0, "Fe": 0.0
            }
            resp = requests.get(f"{self.BASE_URL}/predict", params=params)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("predicted_class", data)
        except requests.ConnectionError:
            self.skipTest("API не запущен")

    def test_predict_kafka(self):
        """Проверка эндпоинта предсказания через Kafka."""
        try:
            # Сначала обучаем модель
            requests.get(f"{self.BASE_URL}/train")
            # Затем предсказываем через Kafka
            params = {
                "RI": 1.52101, "Na": 13.64, "Mg": 4.49,
                "Al": 1.1, "Si": 71.78, "K": 0.06,
                "Ca": 8.75, "Ba": 0.0, "Fe": 0.0
            }
            resp = requests.get(f"{self.BASE_URL}/predict_kafka", params=params)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("predicted_class", data)
            self.assertIn("message", data)
            self.assertEqual(data["message"], "Результат отправлен в Kafka")
        except requests.ConnectionError:
            self.skipTest("API не запущен")


if __name__ == "__main__":
    unittest.main()