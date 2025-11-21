# Стратегия процедурной памяти

Этот документ описывает, что следует хранить в процедурной памяти, как туда попадает информация и какие практики использовать для эффективного управления навыками агентов.

---

## 1. Что хранится в процедурной памяти

Процедурная память — это библиотека **исполнимых навыков и рабочих процессов**, которые агент может вызывать повторно. В отличие от эпизодической (конкретные события) и семантической (общие знания) памяти, процедурная память содержит **алгоритмы действий**.

### 1.1 Типы контента

| Тип | Описание | Пример |
|-----|----------|--------|
| **Исполнимый код** | Функции на Python/JS/SQL, готовые к запуску | `resolve_billing_issue(account_number, issue_type)` |
| **Пошаговые инструкции** | Упорядоченные шаги для выполнения задачи | Workflow по обработке эскалации |
| **SQL-запросы** | Готовые запросы для извлечения данных | Запрос списка активных подписок |
| **API-вызовы** | Шаблоны вызовов внешних сервисов | Интеграция с платёжной системой |
| **Шаблоны промптов** | Стандартные промпты для LLM | Генерация ответа на FAQ |

### 1.2 Метаданные процедуры

Каждая процедура хранит:

- **Идентификаторы**: `procedure_id`, `name` (уникальное имя)
- **Описание**: `description` — что делает процедура
- **Код/шаги**: `code` или `steps` — исполняемая логика
- **Схемы**: `parameters_schema`, `return_schema` (JSON Schema)
- **Теги**: `tags` — для категоризации и поиска
- **Метрики использования**: `execution_count`, `success_rate`, `avg_execution_time_ms`
- **Временные метки**: `created_at`, `last_executed_at`
- **Активность**: `active` — флаг, можно ли использовать процедуру

---

## 2. Как информация попадает в процедурную память

### 2.1 Извлечение из эпизодической памяти

**Сценарий**: Агент замечает повторяющийся паттерн действий в эпизодах.

**Процесс**:

1. Анализ эпизодов через `query_episodes(filter_by_tags=["успешное_решение"])`.
2. Выделение общих шагов из траекторий (`trajectory`).
3. Формирование структуры процедуры:
   ```python
   steps = [
       {"step_number": 1, "action": "check_account_status", "description": "Проверить статус аккаунта"},
       {"step_number": 2, "action": "calculate_refund", "description": "Рассчитать сумму возврата"},
       {"step_number": 3, "action": "process_refund", "description": "Обработать возврат средств"}
   ]
   ```
4. Создание процедуры:
   ```python
   await memory.procedural.create_procedure(
       procedure_id="proc_billing_refund",
       name="billing_refund_workflow",
       description="Обработка возврата средств при переплате",
       agent_id="support_agent",
       steps=steps,
       tags=["billing", "refund", "automation"]
   )
   ```

### 2.2 Ручное создание навыков

**Сценарий**: Разработчик или агент напрямую загружает готовый код.

**Процесс**:

```python
code = """
def resolve_billing_issue(account_number: str, issue_type: str) -> dict:
    if issue_type == "overcharge":
        refund_amount = calculate_refund(account_number)
        process_refund(account_number, refund_amount)
        return {"status": "resolved", "action": "refund", "amount": refund_amount}
    elif issue_type == "missing_payment":
        send_payment_reminder(account_number)
        return {"status": "pending", "action": "reminder_sent"}
    else:
        return {"status": "escalated", "action": "manual_review"}
"""

await memory.procedural.store_procedure(
    procedure_id="proc_resolve_billing",
    name="resolve_billing_issue",
    description="Автоматическое решение биллинговых проблем",
    code=code,
    language="python",
    parameters_schema={
        "type": "object",
        "properties": {
            "account_number": {"type": "string"},
            "issue_type": {"type": "string", "enum": ["overcharge", "missing_payment", "other"]}
        },
        "required": ["account_number", "issue_type"]
    },
    tags=["billing", "support", "automation"]
)
```

### 2.3 Обучение через наблюдение

**Сценарий**: Агент наблюдает за успешным выполнением задачи человеком или другим агентом.

**Процесс**:

1. Эпизод фиксирует детальную траекторию действий эксперта.
2. LLM-агент извлекает шаги и параметры.
3. Генерируется процедура, которая сохраняется с низкой `success_rate` (например, 0.5) для последующей валидации.
4. После нескольких успешных выполнений `success_rate` повышается автоматически через `record_execution`.

### 2.4 Автоматическая кодогенерация

**Сценарий**: Агент генерирует код на основе задачи и семантических знаний.

**Процесс**:

1. Агент получает задачу: "создай функцию для фильтрации активных пользователей".
2. Извлекает релевантные знания из semantic memory.
3. Генерирует код через LLM.
4. Сохраняет процедуру и тестирует её.
5. После успешного тестирования процедура активируется (`active=True`).

---

## 3. Стратегии использования процедурной памяти

### 3.1 Категоризация процедур

Используйте теги для организации навыков:

- **По домену**: `billing`, `support`, `analytics`, `security`
- **По типу**: `automation`, `data_retrieval`, `integration`, `workflow`
- **По языку**: `python`, `sql`, `javascript`
- **По агенту**: `support_agent`, `billing_agent`, `analytics_agent`

### 3.2 Поиск и выбор процедуры

**Запрос по тегам**:
```python
procedures = await memory.procedural.query_procedures(
    filter_by_tags=["billing", "automation"],
    sort_by="success_rate",
    sort_order="desc",
    limit=5
)
```

**Выбор по успешности**:
- Приоритет процедурам с высоким `success_rate` (≥ 0.9).
- Учёт `execution_count` — более проверенные навыки надёжнее.

**Семантический поиск** (если реализован):
- По описанию задачи через эмбеддинги.

### 3.3 Выполнение процедуры

```python
result = await memory.procedural.execute_procedure(
    name="resolve_billing_issue",
    parameters={"account_number": "12345", "issue_type": "overcharge"}
)
print(result)  # {"status": "resolved", "action": "refund", "amount": 50.0}
```

**Логирование**:
- Каждое выполнение автоматически записывает метрики: `execution_time_ms`, `success`, `outcome`.

### 3.4 Обновление и версионирование

**Деактивация устаревших процедур**:
```python
await memory.procedural.deactivate_procedure("proc_old_billing")
```

**Создание новой версии**:
- Сохраните новую процедуру с суффиксом: `resolve_billing_issue_v2`.
- Постепенно переключайте использование после тестирования.

### 3.5 Анализ производительности

**Мониторинг метрик**:
```python
procedure = await memory.procedural.get_procedure(name="resolve_billing_issue")
print(f"Success rate: {procedure['success_rate']}")
print(f"Avg execution time: {procedure['avg_execution_time_ms']} ms")
print(f"Total executions: {procedure['execution_count']}")
```

**Оптимизация**:
- Если `success_rate < 0.7` — пересмотреть логику.
- Если `avg_execution_time_ms > 1000` — оптимизировать код.

---

## 4. Примеры использования

### 4.1 Автоматизация рутинных задач

**Задача**: Отправка уведомлений пользователям о завершении подписки.

**Процедура**:
```python
await memory.procedural.store_procedure(
    procedure_id="proc_send_expiry_notice",
    name="send_subscription_expiry_notice",
    description="Отправить уведомление о завершении подписки",
    code="""
def send_subscription_expiry_notice(user_id: str, days_left: int):
    user = get_user(user_id)
    send_email(user.email, f'Ваша подписка истекает через {days_left} дней')
    log_notification(user_id, 'expiry_notice')
    return {'status': 'sent', 'user_id': user_id}
""",
    language="python",
    tags=["notification", "automation"]
)
```

### 4.2 Интеграция с внешними API

**Задача**: Получение курса валют.

**Процедура**:
```python
await memory.procedural.store_procedure(
    procedure_id="proc_get_exchange_rate",
    name="get_exchange_rate",
    description="Получить курс валют через API",
    code="""
import requests

def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    response = requests.get(f'https://api.exchangerate.com/v1/rates/{from_currency}')
    data = response.json()
    return data['rates'][to_currency]
""",
    language="python",
    tags=["integration", "currency"]
)
```

### 4.3 Workflow-процедуры

**Задача**: Обработка нового заказа.

**Процедура**:
```python
await memory.procedural.create_procedure(
    procedure_id="proc_process_order",
    name="process_new_order",
    description="Полный workflow обработки нового заказа",
    agent_id="order_agent",
    steps=[
        {"step_number": 1, "action": "validate_order", "description": "Проверить данные заказа"},
        {"step_number": 2, "action": "check_inventory", "description": "Проверить наличие на складе"},
        {"step_number": 3, "action": "process_payment", "description": "Обработать платёж"},
        {"step_number": 4, "action": "create_shipment", "description": "Создать отгрузку"},
        {"step_number": 5, "action": "notify_customer", "description": "Уведомить клиента"}
    ],
    tags=["orders", "workflow", "automation"]
)
```

### 4.4 SQL-запросы

**Задача**: Извлечь список активных пользователей.

**Процедура**:
```python
await memory.procedural.store_procedure(
    procedure_id="proc_get_active_users",
    name="get_active_users",
    description="Получить список активных пользователей за последние 30 дней",
    code="SELECT user_id, email, last_login FROM users WHERE last_login > NOW() - INTERVAL '30 days' AND status = 'active'",
    language="sql",
    tags=["data_retrieval", "users"]
)
```

---

## 5. Лучшие практики

### 5.1 Проектирование процедур

- **Одна процедура — одна задача**: Не создавайте «универсальные» процедуры, делающие всё.
- **Явные параметры**: Используйте `parameters_schema` для валидации входных данных.
- **Обработка ошибок**: Код должен включать try-except и возвращать статус выполнения.
- **Документирование**: Описание должно быть понятным и полным.

### 5.2 Управление жизненным циклом

- **Тестирование перед активацией**: Новые процедуры запускайте в изолированной среде.
- **Постепенное внедрение**: Начните с низкого `success_rate`, повышайте после валидации.
- **Деактивация устаревших**: Регулярно ревьюйте и удаляйте неиспользуемые процедуры.
- **Версионирование**: При изменении логики создавайте новую версию, а не перезаписывайте старую.

### 5.3 Мониторинг и оптимизация

- **Отслеживание метрик**: Регулярно проверяйте `success_rate`, `execution_time`, `usage_count`.
- **Анализ ошибок**: Логируйте причины неудач (`error` в `record_execution`).
- **Оптимизация кода**: Если время выполнения растёт, рефакторьте процедуру.
- **A/B-тестирование**: Запускайте альтернативные версии процедур параллельно и сравнивайте результаты.

### 5.4 Безопасность

- **Ограничение прав выполнения**: Используйте песочницы для выполнения кода.
- **Валидация входных данных**: Никогда не доверяйте параметрам без проверки схемы.
- **Аудит**: Логируйте все выполнения процедур для трекинга.

---

## 6. Интеграция с другими типами памяти

### 6.1 Эпизодическая → Процедурная

- Эпизод фиксирует успешное решение задачи → создаётся процедура.
- В процедуре указывается `metadata.source_episode_id` для трассировки.

### 6.2 Семантическая → Процедурная

- Семантическая память предоставляет факты/знания, необходимые для процедуры.
- Процедура может запрашивать знания во время выполнения.

### 6.3 Процедурная → Эпизодическая

- Каждое выполнение процедуры может создавать эпизод для аудита:
  ```python
  await memory.create_episode(
      episode_id=f"exec_{procedure_id}_{timestamp}",
      context={"agent_id": agent_id, "procedure_id": procedure_id},
      title=f"Выполнение {procedure_name}",
      trajectory=[...],
      outcome=result["status"],
      success=result["status"] == "success"
  )
  ```

---

## 7. Будущие улучшения

- **Автоматическое обучение**: Процедуры самостоятельно адаптируются на основе результатов выполнения.
- **Композиция процедур**: Создание сложных workflow из простых процедур.
- **Семантический поиск процедур**: Поиск по эмбеддингам описаний.
- **Версионный контроль**: Интеграция с Git для управления кодом процедур.
- **Мультиязыковая поддержка**: Расширение поддержки языков (Go, Rust, Shell).

---

## Резюме

Процедурная память — это **каталог исполнимых навыков**, которые агент может вызывать для автоматизации задач. Информация попадает туда через:

1. Извлечение паттернов из эпизодов.
2. Ручную загрузку кода.
3. Обучение через наблюдение.
4. Автоматическую генерацию кода.

**Ключевые принципы**:
- Одна процедура = одна задача.
- Мониторинг метрик (`success_rate`, `execution_time`).
- Версионирование и тестирование перед активацией.
- Интеграция с эпизодической и семантической памятью для обогащения контекста.

