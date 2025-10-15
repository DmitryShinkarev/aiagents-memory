# Memory-Agents Project Structure

```
memory-agents/
│
├── __init__.py                      # Главный модуль пакета
├── LICENSE                          # MIT лицензия
├── README.md                        # Основная документация
├── QUICKSTART.md                    # Быстрый старт
├── PROJECT_STRUCTURE.md             # Структура проекта (этот файл)
├── requirements.txt                 # Python зависимости
├── setup.py                         # Установочный скрипт
├── Makefile                         # Команды для разработки
├── docker-compose.yml               # Docker конфигурация
│
├── config/                          # Конфигурация
│   ├── __init__.py
│   ├── settings.py                  # Настройки приложения (Pydantic)
│   ├── prometheus.yml               # Конфигурация Prometheus
│   └── memory/
│       ├── __init__.py
│       └── working_memory.py        # Конфигурация рабочей памяти
│
├── models/                          # Модели данных
│   ├── __init__.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── episodic.py             # Модель эпизодической памяти
│   │   ├── semantic.py             # Модель семантической памяти
│   │   └── procedural.py           # Модель процедурной памяти
│   └── logging/
│       ├── __init__.py
│       └── event_log.py            # Модель логирования событий
│
├── storage/                         # Слой хранения данных
│   ├── __init__.py
│   ├── redis/
│   │   ├── __init__.py
│   │   └── working_store.py        # Реализация рабочей памяти (Redis)
│   ├── mongodb/
│   │   ├── __init__.py
│   │   ├── episodic_store.py       # Эпизодическая память (MongoDB)
│   │   ├── semantic_store.py       # Семантическая память (MongoDB+Qdrant)
│   │   └── procedural_store.py     # Процедурная память (MongoDB)
│   └── postgresql/
│       ├── __init__.py
│       └── event_logger.py         # Логирование событий (PostgreSQL)
│
├── core/                            # Ядро системы
│   ├── __init__.py
│   └── memory_orchestrator.py      # Центральный оркестратор памяти
│
├── utils/                           # Утилиты
│   ├── __init__.py
│   ├── cache.py                    # Кэширование запросов
│   └── initialization.py           # Инициализация системы
│
├── metrics/                         # Мониторинг и метрики
│   ├── __init__.py
│   └── memory_metrics.py           # Prometheus метрики
│
├── examples/                        # Примеры использования
│   ├── __init__.py
│   └── basic_usage.py              # Базовый пример
│
├── tests/                           # Тесты
│   ├── __init__.py
│   ├── conftest.py                 # Pytest конфигурация
│   └── test_working_memory.py      # Тесты рабочей памяти
│
├── scripts/                         # Вспомогательные скрипты
│   ├── mongo-init.js               # Инициализация MongoDB
│   └── postgres-init.sql           # Инициализация PostgreSQL
│
└── docs/                            # Документация
    ├── ARCHITECTURE.md              # Архитектура системы
    └── GETTING_STARTED.md           # Руководство по началу работы
```

## Ключевые компоненты

### 🎯 Core Components

1. **MemoryOrchestrator** (`core/memory_orchestrator.py`)
   - Центральный координатор всех типов памяти
   - Поиск контекста с приоритизацией
   - Консолидация сессий
   - Периодическое обслуживание

2. **Working Memory** (`storage/redis/working_store.py`)
   - Redis-based кратковременная память
   - Управление сессиями и контекстом
   - Временные переменные с TTL
   - Автоматическое сжатие

3. **Episodic Memory** (`storage/mongodb/episodic_store.py`)
   - Хранение истории взаимодействий
   - Векторный поиск эпизодов
   - Оценка важности и релевантности
   - Временной decay

4. **Semantic Memory** (`storage/mongodb/semantic_store.py`)
   - Гибридное хранилище знаний (MongoDB + Qdrant)
   - Семантический и текстовый поиск
   - Версионирование знаний
   - Статистика доступа

5. **Procedural Memory** (`storage/mongodb/procedural_store.py`)
   - Хранение процедур и шаблонов
   - Метрики производительности
   - Отслеживание успешности
   - Автоматическая деактивация неиспользуемых

6. **Event Logger** (`storage/postgresql/event_logger.py`)
   - Аудит всех операций
   - Аналитика производительности
   - Трассировка ошибок
   - Отчеты по использованию ресурсов

### 📊 Data Models

- **Episode**: Эпизод взаимодействия с метаданными
- **SemanticKnowledge**: Факт или знание с embedding
- **Procedure**: Процедура или шаблон
- **EventLog**: Событие для логирования

### 🛠️ Utilities

- **QueryCache**: Кэширование частых запросов в Redis
- **initialize_memory_system**: Упрощенная инициализация
- **memory_metrics**: Prometheus метрики

### 🐳 Infrastructure

- **Redis**: Рабочая память и кэш
- **MongoDB**: Долговременная память
- **Qdrant**: Векторный поиск
- **PostgreSQL**: Логирование и аналитика

## Паттерны и принципы

### Cognitive Architecture
- Working Memory: Активный контекст
- Episodic Memory: Прошлый опыт
- Semantic Memory: Факты и знания
- Procedural Memory: Навыки и процедуры

### Design Patterns
- **Pattern 4.4 RAG**: Retrieval-Augmented Generation
- **Pattern 4.9 Self-reflection**: Консолидация сессий
- **Pattern 4.10 Cross-reflection**: Общая память агентов
- **Pattern 4.11 Human reflection**: Обратная связь

### Best Practices
- Async/await для всех I/O операций
- Connection pooling для БД
- TTL для автоматической очистки
- Индексы для быстрого поиска
- Версионирование знаний
- Метрики для мониторинга

## Масштабирование

### Horizontal Scaling
- MongoDB sharding по `agent_id`
- Redis Cluster для распределенного кэша
- Qdrant кластер для векторного поиска

### Vertical Optimization
- Lua скрипты для атомарных операций
- Составные индексы в MongoDB
- Кэширование результатов запросов
- Партиционирование логов по времени

## Workflow

### Типичный сценарий использования:

1. **Инициализация**: `initialize_memory_system()`
2. **Активная работа**: Сообщения в Working Memory
3. **Поиск контекста**: `retrieve_context()` из всех типов памяти
4. **Консолидация**: `consolidate_session()` в long-term memory
5. **Обслуживание**: `periodic_maintenance()` по расписанию

## Зависимости

### Production
- redis 5.0+
- motor 3.3+
- pymongo 4.6+
- qdrant-client 1.7+
- asyncpg 0.29+
- pydantic 2.5+

### Development
- pytest 7.4+
- pytest-asyncio 0.21+
- black 23.12+
- ruff 0.1+
- mypy 1.8+

## Метрики

### Prometheus Metrics
- `memory_operations_total`: Счетчик операций
- `memory_operation_latency_seconds`: Латентность
- `memory_size_bytes`: Размер памяти
- `cache_hits_total`: Попадания в кэш

## Лицензия

MIT License - см. LICENSE файл

## Версия

0.1.0 - Initial Release


