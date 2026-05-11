"""
Kafka Consumer: читает сообщения из Kafka и сохраняет результаты в БД.
"""
import json
import time
import logging
import asyncio
from kafka import KafkaConsumer
from database import async_session
from sqlalchemy import insert
from database import Predict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def save_to_db(predicted_class: int, features: list):
    """Сохраняет предсказание в БД."""
    async with async_session() as session:
        record = Predict(
            predicted_class=predicted_class,
            RI=features[0], Na=features[1], Mg=features[2], Al=features[3],
            Si=features[4], K=features[5], Ca=features[6], Ba=features[7], Fe=features[8],
        )
        session.add(record)
        await session.commit()
        logger.info(f"Сохранено в БД: class={predicted_class}, RI={features[0]}")


async def main_consumer():
    """Асинхронная обёртка для Consumer."""
    logger.info("Consumer запущен, ожидание Kafka...")

    max_retries = 30
    consumer = None
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                bootstrap_servers='kafka:9092',
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='predict_consumer_group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None
            )
            consumer.topics()
            logger.info("Kafka Consumer подключён")
            break
        except Exception as e:
            logger.warning(f"Попытка {attempt+1}/{max_retries}: Kafka не готова ({e})")
            await asyncio.sleep(2)

    if consumer is None:
        raise RuntimeError("Не удалось подключиться к Kafka")

    # Ждём создания топика predictions
    logger.info("Ожидание топика predictions...")
    for attempt in range(max_retries):
        topics = consumer.topics()
        if 'predictions' in topics:
            logger.info(f"Топик predictions найден (попытка {attempt+1})")
            break
        logger.warning(f"Топик predictions не найден, попытка {attempt+1}/{max_retries}")
        await asyncio.sleep(2)
    else:
        raise RuntimeError("Топик predictions не создан")

    consumer.subscribe(['predictions'])
    logger.info("Подписан на топик predictions, ожидание сообщений...")

    try:
        for message in consumer:
            data = message.value
            predicted_class = data['predicted_class']
            features = [
                data['features']['RI'], data['features']['Na'],
                data['features']['Mg'], data['features']['Al'],
                data['features']['Si'], data['features']['K'],
                data['features']['Ca'], data['features']['Ba'],
                data['features']['Fe']
            ]
            logger.info(f"Получено: class={predicted_class}, offset={message.offset}")
            await save_to_db(predicted_class, features)
            await asyncio.sleep(0.1)  # даём время на обработку
    except KeyboardInterrupt:
        logger.info("Consumer остановлен")
    finally:
        consumer.close()


if __name__ == "__main__":
    asyncio.run(main_consumer())