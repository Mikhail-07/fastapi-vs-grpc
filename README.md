# Инструкция по нагрузочному тестированию FastAPI REST vs gRPC

## Предварительные требования

1. Python 3.8+
2. Установленные зависимости для обоих проектов
3. Запущенные серверы:
   - FastAPI REST API на порту 8000
   - gRPC сервер на порту 50051

## Установка зависимостей для нагрузочного тестирования

```bash
pip install -r requirements_load_testing.txt
```

## Подготовка серверов

### 1. Запуск FastAPI сервера

```bash
cd fastapi-swagger
python main.py
```

Или с uvicorn:
```bash
cd fastapi-swagger
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Запуск gRPC сервера

```bash
cd rpc-grpc-protobuf/glossary_grpc_project/glossary_service
python glossary.py
```

### 3. Инициализация баз данных (если необходимо)

```bash
# FastAPI
cd fastapi-swagger
python init_db.py

# gRPC
cd rpc-grpc-protobuf/glossary_grpc_project/glossary_service
python init_db.py
```

## Запуск нагрузочных тестов

### Вариант 1: Использование Python скрипта (рекомендуется, кроссплатформенно)

```bash
python run_tests.py
```

### Вариант 2: Использование shell скрипта (Linux/Mac)

```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Вариант 3: Использование batch скрипта (Windows)

```bash
run_tests.bat
```

## Запуск отдельных тестов

### Тестирование только REST API

```bash
# Лёгкая нагрузка
LOCUST_USER_CLASS=RestUser locust --headless --users 10 --spawn-rate 2 --run-time 2m -f locustfile.py --html rest_light.html --csv rest_light

# Рабочая нагрузка
LOCUST_USER_CLASS=RestUser locust --headless --users 100 --spawn-rate 10 --run-time 5m -f locustfile.py --html rest_normal.html --csv rest_normal
```

### Тестирование только gRPC API

```bash
# Лёгкая нагрузка
LOCUST_USER_CLASS=GrpcUser locust --headless --users 10 --spawn-rate 2 --run-time 2m -f locustfile.py --html grpc_light.html --csv grpc_light

# Рабочая нагрузка
LOCUST_USER_CLASS=GrpcUser locust --headless --users 100 --spawn-rate 10 --run-time 5m -f locustfile.py --html grpc_normal.html --csv grpc_normal
```

### Интерактивный режим Locust

```bash
# REST
LOCUST_USER_CLASS=RestUser locust -f locustfile.py --host http://localhost:8000

# gRPC
LOCUST_USER_CLASS=GrpcUser locust -f locustfile.py --host http://localhost:8000
```

Затем откройте http://localhost:8089 в браузере для веб-интерфейса Locust.

## Анализ результатов

После завершения всех тестов запустите скрипт сравнения:

```bash
python compare_results.py
```

Это создаст файл `LOAD_TESTING_REPORT.md` с детальным сравнением результатов.

## Структура результатов

Результаты сохраняются в директории `load_test_results/`:

```
load_test_results/
├── light_load_RestUser/
│   ├── report.html
│   ├── results_requests.csv
│   ├── results_stats.csv
│   └── results_failures.csv
├── light_load_GrpcUser/
│   └── ...
├── normal_load_RestUser/
│   └── ...
└── ...
```

## Тестовые сценарии

### 1. Лёгкая нагрузка (Light Load)
- **Назначение**: Sanity check, проверка работоспособности
- **Параметры**: 10 пользователей, 2 users/sec, 2 минуты

### 2. Рабочая нагрузка (Normal Load)
- **Назначение**: Нормальный режим работы
- **Параметры**: 100 пользователей, 10 users/sec, 5 минут

### 3. Стресс-тест (Stress Load)
- **Назначение**: Приближение к пиковой нагрузке
- **Параметры**: 500 пользователей, 50 users/sec, 10 минут

### 4. Тест на стабильность (Stability Load)
- **Назначение**: Проверка деградации при длительной нагрузке
- **Параметры**: 100 пользователей, 5 users/sec, 30 минут

## Собираемые метрики

- **RPS** (Requests Per Second) - запросов в секунду
- **Среднее время ответа** - средняя латентность
- **Медиана, P95, P99** - перцентили латентности
- **Количество ошибок** - общее число и процент ошибок
- **Время до деградации** - момент начала деградации производительности

## Устранение неполадок

### Ошибка подключения к серверу

Убедитесь, что оба сервера запущены:
- FastAPI: `curl http://localhost:8000/`
- gRPC: проверьте логи сервера

### Ошибки импорта protobuf

Убедитесь, что protobuf файлы сгенерированы:
```bash
cd rpc-grpc-protobuf/glossary_grpc_project
# Windows
generate_proto.bat
# Linux/Mac
chmod +x generate_proto.sh
./generate_proto.sh
```

### Проблемы с базой данных

Убедитесь, что базы данных инициализированы и содержат тестовые данные.

## Примечания

- Тесты создают временные термины с уникальными именами
- При параллельном запуске нескольких тестов могут возникать конфликты
- Рекомендуется запускать тесты последовательно для каждого протокола
- Для точных результатов убедитесь, что серверы запущены на отдельной машине или с достаточными ресурсами

