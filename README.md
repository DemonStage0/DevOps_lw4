# DevOps_lw3 - Glass Classification ML Pipeline с HashiCorp Vault

## Описание проекта
Проект реализует классический жизненный цикл разработки ML модели для классификации типов стекла с использованием CI/CD пайплайна и хранилища секретов. Модель классифицирует стекло по 7 классам на основе 9 химических признаков. Данные хранятся в базе данных PostgreSQL, секреты подключения защищены HashiCorp Vault, а сервис модели реализован с использованием FastAPI и SQLAlchemy.

**Ключевое отличие от DevOps_lw2:** все секреты (логин, пароль, хост БД) вынесены в HashiCorp Vault и не хранятся в файлах проекта.

## Структура проекта
```
DevOps_lw3/
├── CI/
│   └── Jenkinsfile          # CI пайплайн
├── CD/
│   └── Jenkinsfile          # CD пайплайн
├── data/
│   ├── glass.csv            # Исходный датасет
│   └── init.sql             # SQL-скрипт создания таблиц
├── src/
│   ├── unit_tests/
│   │   ├── test_api.py          # Тесты API эндпоинтов
│   │   └── test_training.py     # Тесты обучения
│   ├── app.py               # FastAPI приложение
│   ├── config.py            # Получение секретов из Vault
│   ├── csv_to_db.py         # Скрипт переноса данных из CSV в PostgreSQL
│   ├── database.py          # Модели SQLAlchemy и подключение к БД
│   ├── logger.py            # Модуль логирования
│   ├── predict.py           # Класс для предсказаний
│   ├── preprocess.py        # Предобработка данных
│   └── train.py             # Обучение модели
├── vault/
│   └── init-vault.sh        # Скрипт инициализации Vault и записи секретов
├── .gitignore
├── config.ini               # Гиперпараметры модели
├── docker-compose.yml       # Конфигурация сервисов
├── Dockerfile               # Сборка Docker образа
├── README.md
└── requirements.txt         # Зависимости проекта
```

## Установка и запуск

### Предварительные требования
- Docker и Docker Compose
- Git

### Быстрый запуск (рекомендуется)
```bash
# Клонирование репозитория
git clone https://github.com/DemonStage0/DevOps_lw3.git
cd DevOps_lw3

# Запуск всех сервисов (Vault + PostgreSQL + инициализация БД + FastAPI)
docker-compose up -d --build
```

### Порядок запуска сервисов
1. **HashiCorp Vault** — контейнер `devops_lw3-vault` (dev-режим, порт 8200)
2. **Vault Init** — контейнер `devops_lw3-vault-init` записывает секреты БД в Vault
3. **PostgreSQL** — контейнер `glass_db` с автоматическим созданием таблиц через `init.sql`
4. **Инициализация БД** — контейнер `glass_init` получает секреты из Vault и переносит данные из `glass.csv` в таблицу `glass`
5. **FastAPI** — контейнер `devops_lw3-web` получает секреты из Vault и запускает API на порту 8000

### Локальный запуск (для разработки)
```bash
# Требуется запущенный Vault на localhost:8200
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
Ответ: {"message": "Модель обучена успешно. F1 = 0.9761"}
Примечание: данные для обучения загружаются из таблицы glass в PostgreSQL
```

### Предсказание класса стекла
```
GET /predict?RI=1.52101&Na=13.64&Mg=4.49&Al=1.1&Si=71.78&K=0.06&Ca=8.75&Ba=0.0&Fe=0.0
Ответ: {"predicted_class": 1}
```
Все 9 параметров обязательны, имеют значения по умолчанию.

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

### Ручная проверка секретов
```bash
# Из контейнера
docker-compose exec vault vault kv get secret/db

# С хоста
curl -H "X-Vault-Token: devops-lw3-root-token" http://localhost:8200/v1/secret/data/db
```

## База данных

### Структура таблиц
**glass** — обучающие данные (заполняется из `glass.csv`):
- id, RI, Na, Mg, Al, Si, K, Ca, Ba, Fe, Type

**predict** — результаты предсказаний:
- id, predicted_class, RI, Na, Mg, Al, Si, K, Ca, Ba, Fe, timestamp

### Подключение
Приложение получает параметры подключения из Vault при старте. Никакие `.env` файлы не используются в production.

## Тестирование

### Unit-тесты (внутри контейнера)
```bash
docker-compose exec web python -m pytest src/unit_tests/ -v
```

### Unit-тесты (локально)
```bash
# Требуется запущенный Vault
pytest src/ -v
```

### Функциональные тесты API
```bash
curl http://localhost:8000/
curl http://localhost:8000/train
curl "http://localhost:8000/predict?RI=1.52101&Na=13.64&Mg=4.49&Al=1.1&Si=71.78&K=0.06&Ca=8.75&Ba=0.0&Fe=0.0"
```

## CI/CD Pipeline

### CI Pipeline (Jenkins)
- Клонирование репозитория из GitHub
- Сборка Docker образов для сервисов
- Запуск контейнеров (Vault + PostgreSQL + FastAPI)
- Ожидание инициализации Vault
- Запуск unit-тестов внутри контейнера
- Функциональное тестирование API эндпоинтов
- Публикация образа в Docker Hub (`demonstage/devops_lw3`)

### CD Pipeline (Jenkins)
- Загрузка образов из Docker Hub
- Запуск полного стека (Vault + БД + приложение)
- Функциональное тестирование эндпоинтов
- Проверка корректности предсказаний
- Автозапуск после успешного CI пайплайна

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
- **HashiCorp Vault 1.15** (хранилище секретов)
- **Pydantic Settings** (управление конфигурацией)
- **Docker** + Docker Compose (контейнеризация)
- **Jenkins** (CI/CD пайплайны)
- **Git** + GitHub (контроль версий)