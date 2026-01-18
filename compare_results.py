#!/usr/bin/env python3
"""
Script to analyze and compare load test results between REST and gRPC
"""
import os
import csv
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict


RESULTS_DIR = "load_test_results"
OUTPUT_FILE = "LOAD_TESTING_REPORT.md"


def load_csv_results(results_dir):
    """Load CSV results from Locust output"""
    results = {}
    
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            if file.startswith("results_requests") and file.endswith(".csv"):
                # Extract test name and protocol from directory structure
                # Format: {test_name}_{user_class}/results_requests.csv
                dir_name = os.path.basename(root)
                parts = dir_name.split("_")
                if len(parts) >= 2:
                    test_name = "_".join(parts[:-1])
                    protocol = parts[-1]
                    
                    filepath = os.path.join(root, file)
                    try:
                        df = pd.read_csv(filepath)
                        if test_name not in results:
                            results[test_name] = {}
                        results[test_name][protocol] = df
                    except Exception as e:
                        print(f"Error loading {filepath}: {e}")
    
    return results


def calculate_metrics(df):
    """Calculate metrics from a DataFrame"""
    if df.empty:
        return {}
    
    metrics = {
        "total_requests": int(df["Request Count"].sum()),
        "total_failures": int(df["Failure Count"].sum()),
        "avg_response_time": float(df["Average Response Time"].mean()),
        "median_response_time": float(df["Median Response Time"].median()),
        "min_response_time": float(df["Min Response Time"].min()),
        "max_response_time": float(df["Max Response Time"].max()),
    }
    
    # Calculate percentiles if available
    if "95% Response Time" in df.columns:
        metrics["p95_response_time"] = float(df["95% Response Time"].median())
    if "99% Response Time" in df.columns:
        metrics["p99_response_time"] = float(df["99% Response Time"].median())
    
    # Calculate RPS (Requests Per Second)
    if "Requests/s" in df.columns:
        metrics["avg_rps"] = float(df["Requests/s"].mean())
        metrics["max_rps"] = float(df["Requests/s"].max())
    
    # Calculate error rate
    total = metrics["total_requests"]
    failures = metrics["total_failures"]
    metrics["error_rate"] = (failures / total * 100) if total > 0 else 0
    
    return metrics


def generate_comparison_report(results):
    """Generate a markdown report comparing REST and gRPC results"""
    
    report = """# Отчет о нагрузочном тестировании: FastAPI REST vs gRPC

## Описание тестов

Проведено сравнение производительности двух реализаций API для работы с глоссарием терминов:
- **FastAPI REST API** (порт 8000)
- **gRPC API** (порт 50051)

### Тестовые сценарии

1. **Лёгкая нагрузка (Light Load)** - Sanity check
   - Пользователей: 10
   - Скорость подъёма: 2 users/sec
   - Длительность: 2 минуты

2. **Рабочая нагрузка (Normal Load)** - Нормальный режим
   - Пользователей: 100
   - Скорость подъёма: 10 users/sec
   - Длительность: 5 минут

3. **Стресс-тест (Stress Load)** - Приближение к пику
   - Пользователей: 500
   - Скорость подъёма: 50 users/sec
   - Длительность: 10 минут

4. **Тест на стабильность (Stability Load)** - Длительная нагрузка
   - Пользователей: 100
   - Скорость подъёма: 5 users/sec
   - Длительность: 30 минут

### Тестовые операции

- **Лёгкие операции (60% запросов)**:
  - GET /terms (REST) / ListTerms (gRPC) - получение всех терминов
  - GET /terms/{keyword} (REST) / GetTerm (gRPC) - получение одного термина

- **Средние операции (30% запросов)**:
  - GET /terms/search?q={query} (REST) / SearchTerms (gRPC) - поиск с LIKE-запросом

- **Операции записи (10% запросов)**:
  - POST /terms (REST) / AddTerm (gRPC) - создание нового термина

---

## Результаты тестирования

"""
    
    # Process each test scenario
    for test_name in sorted(results.keys()):
        test_results = results[test_name]
        report += f"### {test_name.replace('_', ' ').title()}\n\n"
        
        if "RestUser" in test_results and "GrpcUser" in test_results:
            rest_metrics = calculate_metrics(test_results["RestUser"])
            grpc_metrics = calculate_metrics(test_results["GrpcUser"])
            
            report += "#### Метрики производительности\n\n"
            report += "| Метрика | REST (FastAPI) | gRPC | Разница |\n"
            report += "|---------|----------------|------|----------|\n"
            
            # Compare metrics
            metrics_to_compare = [
                ("Среднее время ответа (мс)", "avg_response_time"),
                ("Медианное время ответа (мс)", "median_response_time"),
                ("P95 время ответа (мс)", "p95_response_time"),
                ("P99 время ответа (мс)", "p99_response_time"),
                ("Средний RPS", "avg_rps"),
                ("Максимальный RPS", "max_rps"),
                ("Всего запросов", "total_requests"),
                ("Ошибок", "total_failures"),
                ("Процент ошибок (%)", "error_rate"),
            ]
            
            for label, metric_key in metrics_to_compare:
                rest_val = rest_metrics.get(metric_key, "N/A")
                grpc_val = grpc_metrics.get(metric_key, "N/A")
                
                if rest_val != "N/A" and grpc_val != "N/A":
                    if isinstance(rest_val, (int, float)) and isinstance(grpc_val, (int, float)):
                        diff = grpc_val - rest_val
                        diff_pct = (diff / rest_val * 100) if rest_val != 0 else 0
                        diff_str = f"{diff:+.2f} ({diff_pct:+.1f}%)"
                    else:
                        diff_str = "N/A"
                else:
                    diff_str = "N/A"
                
                rest_str = f"{rest_val:.2f}" if isinstance(rest_val, float) else str(rest_val)
                grpc_str = f"{grpc_val:.2f}" if isinstance(grpc_val, float) else str(grpc_val)
                
                report += f"| {label} | {rest_str} | {grpc_str} | {diff_str} |\n"
            
            report += "\n"
            
            # Analysis
            report += "#### Анализ\n\n"
            
            if rest_metrics.get("avg_response_time") and grpc_metrics.get("avg_response_time"):
                if grpc_metrics["avg_response_time"] < rest_metrics["avg_response_time"]:
                    improvement = ((rest_metrics["avg_response_time"] - grpc_metrics["avg_response_time"]) / 
                                  rest_metrics["avg_response_time"] * 100)
                    report += f"- gRPC показывает **{improvement:.1f}%** лучшее среднее время ответа\n"
                else:
                    improvement = ((grpc_metrics["avg_response_time"] - rest_metrics["avg_response_time"]) / 
                                  grpc_metrics["avg_response_time"] * 100)
                    report += f"- REST показывает **{improvement:.1f}%** лучшее среднее время ответа\n"
            
            if rest_metrics.get("avg_rps") and grpc_metrics.get("avg_rps"):
                if grpc_metrics["avg_rps"] > rest_metrics["avg_rps"]:
                    improvement = ((grpc_metrics["avg_rps"] - rest_metrics["avg_rps"]) / 
                                  rest_metrics["avg_rps"] * 100)
                    report += f"- gRPC обрабатывает **{improvement:.1f}%** больше запросов в секунду\n"
                else:
                    improvement = ((rest_metrics["avg_rps"] - grpc_metrics["avg_rps"]) / 
                                  grpc_metrics["avg_rps"] * 100)
                    report += f"- REST обрабатывает **{improvement:.1f}%** больше запросов в секунду\n"
            
            report += "\n"
        else:
            report += "Данные для сравнения недоступны.\n\n"
    
    # Overall conclusions
    report += """---

## Общие выводы

### Производительность

1. **Пропускная способность (RPS)**:
   - gRPC обычно показывает более высокую пропускную способность благодаря бинарной сериализации Protocol Buffers
   - REST использует JSON, который более читаем, но менее эффективен по размеру

2. **Латентность (время ответа)**:
   - gRPC демонстрирует более низкую латентность, особенно при больших нагрузках
   - HTTP/2 в gRPC обеспечивает мультиплексирование запросов
   - REST может иметь более высокую латентность из-за overhead HTTP заголовков

3. **Размер сообщений**:
   - Protocol Buffers более компактны, чем JSON
   - Это влияет на network overhead и время передачи данных

4. **Сериализация**:
   - Protocol Buffers: бинарная сериализация, быстрее
   - JSON: текстовая сериализация, медленнее, но более читаема

### Network Overhead

- **REST (HTTP/1.1)**: Каждый запрос требует полного HTTP заголовка
- **gRPC (HTTP/2)**: Мультиплексирование, меньше overhead на соединение
- **Compression**: gRPC поддерживает встроенное сжатие

### Масштабируемость

- При увеличении числа пользователей gRPC показывает лучшую стабильность
- REST может деградировать быстрее при пиковых нагрузках

### Рекомендации

- **Использовать gRPC** для:
  - Микросервисной архитектуры
  - Высоконагруженных систем
  - Систем, требующих низкой латентности
  - Внутренних сервисов

- **Использовать REST** для:
  - Публичных API
  - Интеграции с веб-приложениями
  - Систем, где важна читаемость и простота отладки
  - Систем с простыми требованиями к производительности

---

## Метрики и данные

Все детальные метрики сохранены в директории `load_test_results/`.
HTML отчеты доступны для каждого теста в соответствующих поддиректориях.

"""
    
    return report


def main():
    """Main function"""
    if not os.path.exists(RESULTS_DIR):
        print(f"Results directory '{RESULTS_DIR}' not found.")
        print("Please run load tests first using run_tests.py")
        return
    
    print("Loading test results...")
    results = load_csv_results(RESULTS_DIR)
    
    if not results:
        print("No test results found.")
        return
    
    print(f"Found results for {len(results)} test scenarios")
    print("Generating comparison report...")
    
    report = generate_comparison_report(results)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Report generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

