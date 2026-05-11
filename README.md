# DevOps_lw4 - Glass Classification ML Pipeline с Kafka и HashiCorp Vault

## Описание проекта
Проект расширяет DevOps_lw3, добавляя **Kafka** как промежуточный слой между базой данных и моделью машинного обучения. Реализован полный event-driven pipeline: Producer читает данные из БД, делает предсказания и отправляет результаты в Kafka, а Consumer получает их и сохраняет в БД. Все секреты подключения к БД защищены HashiCorp Vault.

**Ключевое отличие от DevOps_lw3:**
- Добавлен Kafka в качестве message broker
- Реализованы Producer (отправка предсказаний в Kafka) и Consumer (сохранение результатов в БД)
- Новый эндпоинт `/predict_kafka` для предсказаний через Kafka pipeline
- Kafka работает в режиме KRaft (без Zookeeper)

**Сервисы:**
- **Vault** — хранилище секретов БД
- **PostgreSQL** — таблицы `glass` (данные) и `predict` (результаты)
- **Kafka (KRaft)** — брокер сообщений
- **FastAPI (web)** — REST API
- **Producer** — делает predict и отправляет в Kafka
- **Consumer** — читает Kafka и сохраняет в БД

## Структура проекта
```
DevOps_lw4/
├── CI/
│   └── Jenkinsfile              # CI пайплайн
├── CD/
│   └── Jenkinsfile              # CD пайплайн
├── data/
│   ├── glass.csv                # Исходный датасет
│   └── init.sql                 # SQL-скрипт создания таблиц
├── src/
│   ├── unit_tests/
│   │   ├── test_api.py          # Тесты API эндпоинтов
│   │   ├── test_predict.py      # Тесты предиктора
│   │   ├── test_preprocess.py   # Тесты предобработки
│   │   └── test_training.py     # Тесты обучения
│   ├── app.py                   # FastAPI приложение
│   ├── config.py                # Получение секретов из Vault
│   ├── consumer.py              # Kafka Consumer (сохранение в БД)
│   ├── csv_to_db.py             # Скрипт переноса данных из CSV в PostgreSQL
│   ├── database.py              # Модели SQLAlchemy и подключение к БД
│   ├── logger.py                # Модуль логирования
│   ├── predict.py               # Класс для предсказаний
│   ├── preprocess.py            # Предобработка данных
│   ├── producer.py              # Kafka Producer (predict + отправка в Kafka)
│   └── train.py                 # Обучение модели
├── vault/
│   └── init-vault.sh            # Скрипт инициализации Vault и записи секретов
├── .dockerignore
├── .gitignore
├── config.ini                   # Гиперпараметры модели
├── docker-compose.yml           # Конфигурация сервисов
├── Dockerfile                   # Сборка Docker образа
├── README.md
└── requirements.txt             # Зависимости проекта
```

## Установка и запуск

### Предварительные требования
- Docker и Docker Compose
- Git

### Быстрый запуск
```bash
# Клонирование репозитория
git clone https://github.com/DemonStage0/DevOps_lw4.git
cd DevOps_lw4

# Запуск всех сервисов
docker-compose up -d --build
```

### Порядок запуска сервисов
1. **HashiCorp Vault** — контейнер `devops_lw4-vault` (dev-режим, порт 8200)
2. **Vault Init** — контейнер `devops_lw4-vault-init` записывает секреты БД в Vault
3. **PostgreSQL** — контейнер `glass_db` с автоматическим созданием таблиц через `init.sql`
4. **Инициализация БД** — контейнер `glass_init` получает секреты из Vault и переносит данные из `glass.csv`
5. **Kafka** — контейнер `devops_lw4-kafka` в режиме KRaft (порт 9092)
6. **Consumer** — контейнер `devops_lw4-consumer` ожидает сообщения из Kafka
7. **FastAPI** — контейнер `devops_lw4-web` запускает API на порту 8000

### Локальный запуск (для разработки)
```bash
# Требуется запущенный Vault на localhost:8200 и Kafka на localhost:9092
pip install -r requirements.txt
set VAULT_ADDR=http://localhost:8200
set VAULT_TOKEN=devops-lw3-root-token
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health check
```
GET /
Ответ: {"message": "Glass Classification API is running", "version": "2.0.0"}
```

### Обучение модели
```
GET /train
Ответ: {"message": "Модель обучена успешно. F1 = 1.0000"}
Примечание: данные для обучения загружаются из таблицы glass в PostgreSQL
```

### Предсказание класса стекла (без Kafka)
```
GET /predict?RI=1.52101&Na=13.64&Mg=4.49&Al=1.1&Si=71.78&K=0.06&Ca=8.75&Ba=0.0&Fe=0.0
Ответ: {"predicted_class": 2}
```
Все 9 параметров обязательны, имеют значения по умолчанию. Результат сразу сохраняется в БД.

### Предсказание класса стекла (через Kafka)
```
GET /predict_kafka?RI=1.52101&Na=13.64&Mg=4.49&Al=1.1&Si=71.78&K=0.06&Ca=8.75&Ba=0.0&Fe=0.0
Ответ: {"predicted_class": 2, "message": "Результат отправлен в Kafka"}
```
Модель делает predict, результат отправляется в Kafka. Consumer в фоне сохранит его в таблицу `predict`.

### Классы стекла
```
1 - building_windows_float_processed
2 - building_windows_non_float_processed
3 - vehicle_windows_float_processed
4 - vehicle_windows_non_float_processed (отсутствует в датасете)
5 - containers
6 - tableware
7 - headlamps
```

## Kafka Pipeline

### Топик
- **Название:** `predictions`
- **Создаётся автоматически** при первой отправке сообщения

### Producer
- Читает данные из таблицы `glass` через секреты Vault
- Делает predict моделью RandomForest
- Отправляет результат в топик `predictions`

### Consumer
- Подписан на топик `predictions`
- Читает сообщения и сохраняет результат в таблицу `predict`
- Автоматически перезапускается при падении

### Проверка Kafka
```bash
# Проверить топики
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Проверить логи Consumer
docker-compose logs consumer
```

## Хранилище секретов (HashiCorp Vault)

### Конфигурация
- **Адрес:** http://vault:8200 (внутри Docker сети), http://localhost:8200 (с хоста)
- **Root Token:** `devops-lw3-root-token` (захардкожен в контейнере Vault)
- **Режим:** Development (in-memory, данные не сохраняются между перезапусками)

### Сохраняемые секреты
В Vault по пути `secret/data/db` хранятся:
```
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
DB_NAME=glass_db
```

### Получение секретов в коде
```python
from src.config import get_db_url
database_url = get_db_url()  # автоматически получает секреты из Vault
```

## База данных

### Структура таблиц
**glass** — обучающие данные (заполняется из `glass.csv`):
- id, RI, Na, Mg, Al, Si, K, Ca, Ba, Fe, Type

**predict** — результаты предсказаний:
- id, predicted_class, RI, Na, Mg, Al, Si, K, Ca, Ba, Fe, timestamp

### Подключение
Приложение получает параметры подключения из Vault при старте. Никакие `.env` файлы не используются.

## Тестирование

### Unit-тесты (внутри контейнера)
```bash
docker-compose exec web python -m pytest src/unit_tests/ -v
```

### Функциональные тесты API
```bash
# Проверка здоровья
curl http://localhost:8000/

# Обучение модели
curl http://localhost:8000/train

# Предсказание (без Kafka)
curl "http://localhost:8000/predict?RI=1.52&Na=13.5&Mg=3.5&Al=1.4&Si=72.5&K=0.5&Ca=9.0&Ba=0.1&Fe=0.1"

# Предсказание через Kafka
curl "http://localhost:8000/predict_kafka?RI=1.52&Na=13.5&Mg=3.5&Al=1.4&Si=72.5&K=0.5&Ca=9.0&Ba=0.1&Fe=0.1"
```

## CI/CD Pipeline

### CI Pipeline (Jenkins)
- Клонирование репозитория из GitHub
- Сборка Docker образов для всех сервисов
- Запуск контейнеров (Vault + PostgreSQL + Kafka + Consumer + FastAPI)
- Ожидание инициализации Vault и Kafka
- Запуск unit-тестов внутри контейнера
- Функциональное тестирование всех эндпоинтов (`/`, `/train`, `/predict`, `/predict_kafka`)
- Проверка логов Kafka и Consumer
- Публикация образа в Docker Hub (`demonstage/devops_lw4`)

### CD Pipeline (Jenkins)
- Загрузка образов из Docker Hub
- Запуск полного стека (Vault + БД + Kafka + Consumer + приложение)
- Функциональное тестирование эндпоинтов

## Эксперименты
Каждый эксперимент сохраняется в `experiments/exp_N/` и содержит:
- `config.yml` — параметры модели, хэш обученной модели
- `trained_model.pkl` — сериализованная модель RandomForestClassifier
- `metrics.yml` — метрики качества (F1, accuracy)
- `logs.txt` — логи обучения

## Безопасность
- **Все секреты в Vault** — пароли, хосты, порты не хранятся в коде
- **`.env` удалён из репозитория** — добавлен в `.gitignore`
- **Пароль Vault захардкожен** — только для разработки (dev-режим)
- **Инициализация при старте** — `init-vault.sh` автоматически загружает секреты Vault

## Технологии
- **Python 3.12** + scikit-learn (Random Forest Classifier)
- **FastAPI** + Uvicorn (REST API)
- **PostgreSQL 15** (хранение данных и результатов)
- **SQLAlchemy 2.0** + asyncpg (асинхронная работа с БД)
- **Apache Kafka 7.5** (Confluent, режим KRaft)
- **kafka-python** (Producer и Consumer)
- **HashiCorp Vault 1.15** (хранилище секретов)
- **Pydantic Settings** (управление конфигурацией)
- **Docker** + Docker Compose (контейнеризация, 7 сервисов)
- **Jenkins** (CI/CD пайплайны)
- **Git** + GitHub (контроль версий)