# Настройка нагрузочного тестирования завершена

## Выполненные задачи

✅ **Добавлен поисковый эндпоинт в FastAPI**
- Добавлен `GET /terms/search?q={query}` в `fastapi-swagger/main.py`
- Аналогичен `SearchTerms` в gRPC для справедливого сравнения

✅ **Созданы классы пользователей Locust**
- `RestUser` - для тестирования FastAPI REST API
- `GrpcUser` - для тестирования gRPC API
- Реалистичное поведение: пропорции запросов (60% чтение, 30% поиск, 10% запись), паузы 1-3 сек

✅ **Созданы конфигурации тестовых сценариев**
- `locust_config_light.py` - лёгкая нагрузка (10 users, 2 min)
- `locust_config_normal.py` - рабочая нагрузка (100 users, 5 min)
- `locust_config_stress.py` - стресс-тест (500 users, 10 min)
- `locust_config_stability.py` - тест на стабильность (100 users, 30 min)

✅ **Созданы скрипты для запуска тестов**
- `run_tests.py` - кроссплатформенный Python скрипт (рекомендуется)
- `run_tests.sh` - для Linux/Mac
- `run_tests.bat` - для Windows
- Все скрипты включают проверку доступности серверов

✅ **Создан скрипт сравнения результатов**
- `compare_results.py` - автоматически анализирует результаты и создаёт `LOAD_TESTING_REPORT.md`
- Сравнивает метрики: RPS, время ответа, перцентили, ошибки

✅ **Создана документация**
- `README_LOAD_TESTING.md` - подробные инструкции
- `check_servers.py` - утилита для проверки серверов

## Следующие шаги

### 1. Установить зависимости

```bash
pip install -r requirements_load_testing.txt
```

### 2. Запустить серверы

**Терминал 1 - FastAPI:**
```bash
cd fastapi-swagger
python main.py
```

**Терминал 2 - gRPC:**
```bash
cd rpc-grpc-protobuf/glossary_grpc_project/glossary_service
python glossary.py
```

### 3. Проверить серверы

```bash
python check_servers.py
```

### 4. Запустить тесты

```bash
python run_tests.py
```

Это запустит все 4 сценария для обоих протоколов (REST и gRPC).

### 5. Сгенерировать отчёт

```bash
python compare_results.py
```

Отчёт будет сохранён в `LOAD_TESTING_REPORT.md`.

## Структура файлов

```
.
├── locustfile.py                    # Основной файл с классами пользователей
├── locust_config_light.py           # Конфигурация лёгкой нагрузки
├── locust_config_normal.py          # Конфигурация рабочей нагрузки
├── locust_config_stress.py          # Конфигурация стресс-теста
├── locust_config_stability.py       # Конфигурация теста на стабильность
├── run_tests.py                     # Скрипт запуска тестов (Python)
├── run_tests.sh                     # Скрипт запуска тестов (Linux/Mac)
├── run_tests.bat                    # Скрипт запуска тестов (Windows)
├── compare_results.py               # Скрипт сравнения результатов
├── check_servers.py                 # Утилита проверки серверов
├── requirements_load_testing.txt     # Зависимости для нагрузочного тестирования
├── README_LOAD_TESTING.md           # Подробная документация
└── load_test_results/               # Директория с результатами (создаётся автоматически)
```

## Примечания

- Тесты можно запускать по отдельности для каждого протокола
- Используйте переменную окружения `LOCUST_USER_CLASS` для выбора протокола
- Результаты сохраняются в CSV и HTML форматах
- Отчёт генерируется автоматически после запуска `compare_results.py`

## Готово к использованию!

Все компоненты настроены и готовы к запуску. Убедитесь, что оба сервера запущены перед началом тестирования.

