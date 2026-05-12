import sys
import os
from fastapi import FastAPI, HTTPException, Query

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.dirname(__file__))

from logger import Logger
from database import get_glass_data, save_prediction
from preprocess import DataPreprocessor
from train import ModelTrainer
from predict import Predictor
from producer import create_kafka_producer

app = FastAPI(title="Glass Classification API", version="2.0.0")
log = Logger(True).get_logger(__name__)


@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работоспособности."""
    return {"message": "Glass Classification API is running", "version": "2.0.0"}


@app.get("/health")
async def health():
    """Эндпоинт проверки здоровья сервиса."""
    return {"status": "healthy"}


@app.get("/train")
async def train():
    """Обучает модель на данных из БД и сохраняет эксперимент."""
    X, y = await get_glass_data()
    preprocessor = DataPreprocessor()
    X_tr, X_te, y_tr, y_te = await preprocessor.prepare_data(X, y)
    trainer = ModelTrainer()
    result = await trainer.train(X_tr, X_te, y_tr, y_te)
    return {"message": f"Модель обучена успешно. F1 = {result['f1_score']:.4f}"}


@app.get("/predict")
async def predict(
    RI: float = Query(1.52101), Na: float = Query(13.64), Mg: float = Query(4.49),
    Al: float = Query(1.1), Si: float = Query(71.78), K: float = Query(0.06),
    Ca: float = Query(8.75), Ba: float = Query(0.0), Fe: float = Query(0.0),
):
    """Предсказывает класс стекла и сохраняет результат в БД."""
    features = [RI, Na, Mg, Al, Si, K, Ca, Ba, Fe]
    try:
        pred = Predictor().predict(features)
    except FileNotFoundError:
        raise HTTPException(404, "Нет предобученной модели. Сначала вызовите /train")
    await save_prediction(pred, features)
    return {"predicted_class": pred}


@app.get("/predict_kafka")
async def predict_kafka(
    RI: float = Query(1.52101), Na: float = Query(13.64), Mg: float = Query(4.49),
    Al: float = Query(1.1), Si: float = Query(71.78), K: float = Query(0.06),
    Ca: float = Query(8.75), Ba: float = Query(0.0), Fe: float = Query(0.0),
):
    """Предсказывает класс стекла через модель, отправляет результат в Kafka и возвращает ответ."""
    features = [RI, Na, Mg, Al, Si, K, Ca, Ba, Fe]
    try:
        pred = Predictor().predict(features)

        producer = create_kafka_producer()
        message = {
            "predicted_class": int(pred),
            "features": {
                "RI": RI, "Na": Na, "Mg": Mg, "Al": Al, "Si": Si,
                "K": K, "Ca": Ca, "Ba": Ba, "Fe": Fe
            }
        }
        producer.send("predictions", value=message)
        producer.flush()
        producer.close()

        log.info(f"Предсказание отправлено в Kafka: class={pred}")
        return {
            "predicted_class": pred,
            "message": "Результат отправлен в Kafka"
        }
    except FileNotFoundError:
        raise HTTPException(404, "Нет предобученной модели. Сначала вызовите /train")
    except Exception as e:
        log.error(f"Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))