import os
import json
import time
import logging
import pandas as pd
from sklearn.preprocessing import StandardScaler
from kafka import KafkaProducer
from database import get_glass_data
from predict import Predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_kafka_producer() -> KafkaProducer:
    """Создаёт Kafka Producer с ожиданием готовности брокера."""
    max_retries = 30
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
            producer.bootstrap_connected()
            logger.info("Kafka Producer подключён")
            return producer
        except Exception as e:
            logger.warning(f"Попытка {attempt + 1}/{max_retries}: Kafka не готова ({e})")
            time.sleep(2)
    raise RuntimeError("Не удалось подключиться к Kafka")


async def run_producer():
    """Основная логика Producer: данные → модель → Kafka."""
    logger.info("Producer запущен")

    # Получаем данные из БД
    X, y_true = await get_glass_data()
    if not X:
        logger.warning("Нет данных в таблице glass")
        return {"status": "empty", "message": "Нет данных для предсказания"}

    # Загружаем модель
    predictor = Predictor()
    model, _ = predictor.load_latest_model()
    if model is None:
        raise FileNotFoundError("Нет предобученной модели")

    # Загружаем scaler из сохранённых данных (если есть)
    X_train_path = "data/X_train.csv"
    if os.path.exists(X_train_path):
        X_train_df = pd.read_csv(X_train_path, index_col=0)
        # Обучаем scaler на тренировочных данных
        scaler = StandardScaler()
        scaler.fit(X_train_df)
        # Применяем scaler ко всем данным
        X_scaled = scaler.transform(pd.DataFrame(X, columns=X_train_df.columns))
        predictions = model.predict(X_scaled)
    else:
        # Если нет сохранённых данных — используем Predictor с fit_transform
        predictions = [predictor.predict(features) for features in X]

    # Отправляем в Kafka
    producer = create_kafka_producer()
    topic = "predictions"

    for i, (features, pred_class) in enumerate(zip(X, predictions)):
        message = {
            "id": i,
            "predicted_class": int(pred_class),
            "features": {
                "RI": float(features[0]), "Na": float(features[1]),
                "Mg": float(features[2]), "Al": float(features[3]),
                "Si": float(features[4]), "K": float(features[5]),
                "Ca": float(features[6]), "Ba": float(features[7]),
                "Fe": float(features[8])
            }
        }
        future = producer.send(topic, key=str(i), value=message)
        record_metadata = future.get(timeout=10)
        logger.info(f"Отправлено: offset={record_metadata.offset}")

    producer.flush()
    producer.close()
    logger.info(f"Producer завершил работу: отправлено {len(predictions)} сообщений")
    return {"status": "success", "count": len(predictions)}


if __name__ == "__main__":
    import os

    os.environ['PYTHONPATH'] = '/app'
    import asyncio

    asyncio.run(run_producer())