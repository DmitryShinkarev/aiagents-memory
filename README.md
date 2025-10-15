# Memory Agents - Система памяти для мультиагентных систем

## Описание

Комплексная система памяти для мультиагентных систем, основанная на когнитивной модели человека с четырьмя уровнями памяти:

- **Рабочая память (Working Memory)** - Redis
- **Эпизодическая память (Episodic Memory)** - MongoDB
- **Семантическая память (Semantic Memory)** - MongoDB + Qdrant
- **Процедурная память (Procedural Memory)** - MongoDB

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    USER / API LAYER                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│               MEMORY ORCHESTRATOR                            │
│  - Routing Logic                                             │
│  - Consistency Management                                    │
│  - Priority & Relevance Scoring                              │
└──────┬────────────┬────────────┬─────────────┬──────────────┘
       │            │            │             │
   ┌───▼───┐   ┌───▼───┐   ┌────▼────┐   ┌────▼─────┐
   │Working│   │Episode│   │Semantic │   │Procedural│
   │Memory │   │ Memory│   │ Memory  │   │  Memory  │
   │(Redis)│   │(Mongo)│   │ (Mongo  │   │ (Mongo)  │
   │       │   │       │   │ +Qdrant)│   │          │
   └───────┘   └───────┘   └─────────┘   └──────────┘
       │            │            │             │
       └────────────┴────────────┴─────────────┘
                       │
              ┌────────▼────────┐
              │  LOGGING LAYER  │
              │   (PostgreSQL)  │
              └─────────────────┘
```

## Технологический стек

- **Redis 7.x** - Рабочая память, кэш, сессии
- **MongoDB 7.x** - Долговременная память
- **Qdrant** - Векторный поиск
- **PostgreSQL 16.x** - Логирование и аналитика
- **Python 3.11+** - Основной язык разработки

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск инфраструктуры (Docker)

```bash
docker-compose up -d
```

### 3. Инициализация системы

```python
from memory_agents import initialize_memory_system

# Инициализация с конфигурацией по умолчанию
orchestrator = await initialize_memory_system()
```

### 4. Базовое использование

```python
from memory_agents import MemoryOrchestrator

# Создание сессии и добавление сообщений
session_id = "session_001"
await orchestrator.working.add_message(
    session_id=session_id,
    role="user",
    content="Привет, как дела?"
)

# Поиск контекста для ответа
context = await orchestrator.retrieve_context(
    agent_id="agent_001",
    session_id=session_id,
    query="Как организовать память?",
    max_tokens=4096
)

# Консолидация сессии в долговременную память
await orchestrator.consolidate_session(
    agent_id="agent_001",
    session_id=session_id
)
```

## Структура проекта

```
memory-agents/
├── config/              # Конфигурация
│   ├── settings.py
│   └── memory/
│       └── working_memory.py
├── models/              # Модели данных
│   ├── memory/
│   │   ├── episodic.py
│   │   ├── semantic.py
│   │   └── procedural.py
│   └── logging/
│       └── event_log.py
├── storage/             # Хранилища данных
│   ├── redis/
│   │   └── working_store.py
│   ├── mongodb/
│   │   ├── episodic_store.py
│   │   ├── semantic_store.py
│   │   └── procedural_store.py
│   └── postgresql/
│       └── event_logger.py
├── core/                # Основная логика
│   ├── memory_orchestrator.py
│   └── embedding_service.py
├── utils/               # Утилиты
│   ├── cache.py
│   └── sharding.py
├── metrics/             # Мониторинг
│   └── memory_metrics.py
├── examples/            # Примеры использования
│   └── basic_usage.py
└── tests/               # Тесты
```

## Основные возможности

### Рабочая память (Working Memory)

- Хранение активного контекста сессии
- Автоматическое управление TTL
- Сжатие контекста при достижении лимита
- Временные переменные с TTL

### Эпизодическая память (Episodic Memory)

- История взаимодействий с агентом
- Векторный поиск похожих эпизодов
- Оценка важности и релевантности
- Временной decay для старых эпизодов

### Семантическая память (Semantic Memory)

- Хранение фактов и знаний
- Гибридный поиск (векторный + текстовый)
- Версионирование знаний
- Статистика использования

### Процедурная память (Procedural Memory)

- Шаблоны промптов
- Workflows и инструкции
- Метрики успешности
- Автоматическая оптимизация

### Memory Orchestrator

- Единая точка доступа ко всем типам памяти
- Интеллектуальная приоритизация контекста
- Консолидация сессий
- Периодическое обслуживание

## Конфигурация

Основные параметры конфигурации в `.env`:

```env
# Redis
REDIS_URL=redis://localhost:6379
REDIS_SESSION_TTL=3600

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=agent_memory

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# PostgreSQL
POSTGRES_URL=postgresql://localhost/memory_logs

# Memory limits
WORKING_MEMORY_MAX_MESSAGES=50
WORKING_MEMORY_CONTEXT_WINDOW=8192
EPISODIC_MEMORY_TTL_DAYS=90
SEMANTIC_MEMORY_TTL_DAYS=365
```

## Паттерны из исследования

Реализованные паттерны:
- **Pattern 4.4 RAG**: Семантическая память + Qdrant
- **Pattern 4.9 Self-reflection**: Консолидация сессий
- **Pattern 4.10 Cross-reflection**: Общая память между агентами
- **Pattern 4.11 Human reflection**: Обратная связь пользователей

## Мониторинг и метрики

Система экспортирует метрики в формате Prometheus:

- `memory_operations_total` - Счетчик операций
- `memory_operation_latency_seconds` - Латентность операций
- `memory_size_bytes` - Размер памяти

## Производительность

### Оптимизации:

- Lua-скрипты для атомарных операций в Redis
- Составные индексы в MongoDB
- Кэширование частых запросов
- Шардирование по agent_id
- Партиционирование логов по времени

### Масштабирование:

- Горизонтальное масштабирование MongoDB (sharding)
- Redis Cluster для распределенного кэша
- Qdrant кластер для векторного поиска
- Миграция на ClickHouse для больших объемов логов

## Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием
pytest --cov=memory_agents --cov-report=html

# Только интеграционные тесты
pytest tests/integration/
```

## Разработка

```bash
# Форматирование кода
black .

# Линтинг
ruff check .

# Проверка типов
mypy memory_agents/
```

## Лицензия

MIT License

## Контакты

Для вопросов и предложений создавайте issues в репозитории.


