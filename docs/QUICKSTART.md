# Memory-Agents Quick Start

## 🚀 Быстрый старт за 5 минут

### 1. Запуск инфраструктуры

```bash
# Запустить все сервисы через Docker
docker-compose up -d

# Проверить статус
docker-compose ps
```

### 2. Установка пакета

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 3. Конфигурация

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать .env при необходимости
# По умолчанию настроен на локальные сервисы Docker
```

### 4. Первый запуск

```python
# test_memory.py
import asyncio
from memory_agents import initialize_memory_system

async def main():
    # Инициализация системы
    orchestrator = await initialize_memory_system(agent_id="my_agent")
    
    # Добавление сообщения в рабочую память
    await orchestrator.working.add_message(
        session_id="session_1",
        role="user",
        content="Hello, Memory-Agents!"
    )
    
    # Получение контекста
    context = await orchestrator.working.get_context("session_1")
    print(f"Messages: {len(context)}")
    print(f"Content: {context[0]['content']}")

asyncio.run(main())
```

```bash
# Запустить
python test_memory.py
```

### 5. Запуск примера

```bash
# Полный пример использования
python examples/basic_usage.py
```

## 📚 Основные операции

### Рабочая память (Working Memory)

```python
# Добавить сообщение
await orchestrator.working.add_message(
    session_id="session_1",
    role="user",
    content="Привет!"
)

# Получить контекст
messages = await orchestrator.working.get_context("session_1")

# Временные переменные
await orchestrator.working.set_temp_variable(
    "session_1", "topic", "multi-agent-systems"
)
topic = await orchestrator.working.get_temp_variable("session_1", "topic")
```

### Комплексный поиск контекста

```python
context = await orchestrator.retrieve_context(
    agent_id="my_agent",
    session_id="session_1",
    query="Что мы обсуждали о памяти?",
    max_tokens=4096
)

print(f"Working: {len(context['working'])} items")
print(f"Episodic: {len(context['episodic'])} items")
print(f"Semantic: {len(context['semantic'])} items")
```

### Консолидация сессии

```python
# Перенос из рабочей памяти в долговременную
await orchestrator.consolidate_session(
    agent_id="my_agent",
    session_id="session_1"
)
```

### Добавление знаний

```python
from memory_agents import SemanticKnowledge, KnowledgeType

knowledge = SemanticKnowledge(
    content="Redis - это хранилище данных в памяти",
    knowledge_type=KnowledgeType.FACT,
    source="documentation",
    tags=["redis", "database"]
)

# Требуется сервис эмбеддингов
# embedding = await embedding_service.embed(knowledge.content)
# await orchestrator.semantic.add_knowledge(knowledge, embedding)
```

### Добавление процедур

```python
from memory_agents import Procedure, ProcedureType, ProcedureParameter

procedure = Procedure(
    name="greeting",
    procedure_type=ProcedureType.PROMPT_TEMPLATE,
    description="Шаблон приветствия",
    content="Привет, {name}!",
    parameters=[
        ProcedureParameter(name="name", type="string", required=True)
    ]
)

proc_id = await orchestrator.procedural.save_procedure(procedure)
```

## 🔧 Команды Makefile

```bash
make install        # Установить зависимости
make docker-up      # Запустить Docker сервисы
make docker-down    # Остановить Docker сервисы
make test           # Запустить тесты
make run-example    # Запустить пример
make lint           # Проверить код
make format         # Форматировать код
```

## 📖 Дополнительные ресурсы

- [Полная документация](./docs/GETTING_STARTED.md)
- [Архитектура системы](./docs/ARCHITECTURE.md)
- [Примеры использования](./examples/)

## 🐛 Проблемы?

### Проверка сервисов

```bash
# Redis
redis-cli ping  # Должен вернуть PONG

# MongoDB
mongosh --eval "db.adminCommand('ping')"

# Qdrant
curl http://localhost:6333/health

# PostgreSQL
psql -U postgres -c "SELECT version();"
```

### Логи Docker

```bash
# Все логи
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f mongodb
```

## 📊 Мониторинг

```bash
# Запустить с мониторингом
docker-compose --profile monitoring up -d

# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

## 🎯 Что дальше?

1. Изучите [примеры](./examples/)
2. Прочитайте [архитектуру](./docs/ARCHITECTURE.md)
3. Настройте сервис эмбеддингов для полной функциональности
4. Интегрируйте в свою мультиагентную систему

---

**Версия**: 0.1.0  
**Лицензия**: MIT  
**Документация**: [docs/](./docs/)





