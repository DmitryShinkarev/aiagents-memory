# Контракты взаимодействия слоёв Memory-Agents

Документ описывает, какими структурами данных и обязательствами обмениваются API-слой, бизнес-логика, доменные сервисы и слой хранения.

## 1. Общий поток

1. **API Layer** принимает запросы (REST/gRPC) и приводит их к стабильным моделям (`Universal*Request`), гарантируя валидацию схем и версионирование.
2. **Business Logic Layer** (IdempotencyGuard, RequestValidator, адаптеры) применяет кросс-срезочные правила: идемпотентность, доступ, трансформацию DTO.
3. **Domain Layer** реализует предметные сервисы (`WorkingMemoryService`, `EpisodicMemoryService`, `SemanticMemoryService`, `ProceduralMemoryService`, `FactsService`) и оперирует бизнес-объектами.
4. **Storage Layer** обеспечивает конкретные драйверы (Redis, MongoDB, Qdrant, PostgreSQL), предоставляя абстракции с чёткими контрактами по типам данных и отказоустойчивости.

```
Client → Universal*Request → Business Guards → MemoryService → Storage Client
```

## 2. API Layer Contracts

| Контракт | Назначение | Ключевые поля | Гарантии |
| --- | --- | --- | --- |
| `UniversalEntityWriteRequest` | Запись произвольной сущности | `idempotency_key`, `requesting_agent_id`, `entity_namespace`, `entity_type`, `entity_data`, `access_scope` | Версионированный DTO, строгая схема (Pydantic v2) |
| `UniversalEpisodeWriteRequest` | Создание/обновление эпизода | `EpisodeContext` (user/agent/session), `scope`, `episode_type`, `title`, `trajectory`, `importance`, `metadata` | Согласованный формат траекторий, связь с access scope |
| `UniversalKnowledgeWriteRequest` | Запись знаний | `knowledge_id`, `knowledge`, `source`, `confidence`, `supporting_evidence`, `access_scope` | Поддержка ссылок на эпизоды, temporal scope |
| `EpisodeContext`, `EpisodeTrajectory` | Вспомогательные структуры | Контекст участника, шаг с `timestamp`, `role`, `action`, `content`, `metadata` | ISO-времена, строгие перечисления |

API слой возвращает унифицированные ответы (`UniversalWriteResponse`, `PaginatedResult`, `HealthStatus`), дружелюбные к версионированию.

## 3. Business Logic Layer Contracts

- **IdempotencyGuard**
  - Вход: хэшированный `idempotency_key`, сериализованный запрос.
  - Обязательства: единожды исполнять операцию, возвращать кешированный ответ при повторе, писать метаданные в Redis/PostgreSQL.
- **RequestValidator**
  - Проверяет схемы (Pydantic), бизнес-правила (например, запрет на `team_shared` без `team_id`), rate limit.
  - Выдаёт нормализованный DTO доменному сервису.
- **Contract Adapters**
  - Маппят `Universal*` структуры в внутренние `CreateEpisodeCommand`, `StoreKnowledgeCommand` и т.п.

## 4. Domain Layer Contracts

### WorkingMemoryService
- API: `store_session(session_id, data)`, `get_context(agent_id, session_id=None)`, `cache_retrieval(query_hash, result, ttl)`, `publish_event`, `subscribe_events`.
- Контракт с бизнес-слоем: принимает валидированный `session_data` (dict), TTL, идентификаторы агента/сессии.

### EpisodicMemoryService
- API: `create_episode`, `get_episode`, `query_episodes`.
- Ожидает `EpisodeContext`, `EpisodeTrajectory[]`, числовые поля (`importance`, `user_satisfaction`), optional `embedding`.
- Возвращает DTO эпизода (id, context, scope, trajectory, метрики).

### SemanticMemoryService
- API: `create_knowledge`, `semantic_search`.
- Требует `supporting_evidence` для трассировки, `temporal_scope`, `half_life_days`.
- Возвращает знания + score, опционально с учётом временного затухания.

### ProceduralMemoryService
- API: `store_procedure`, `execute_procedure`.
- Принимает уникальные `procedure_id`/`name`, исходный код (строка), `parameters_schema`/`return_schema` в формате JSON Schema.
- Возвращает ID при записи и структуру результата (status, payload, execution metadata) при выполнении.

### FactsService
- API: `store_fact`, `get_user_profile`, `query_facts`.
- Контракт включает версионирование (`valid_from`, `valid_until`), `confidence`, источник (`SourceType`), список `evidence`.

## 5. Storage Layer Contracts

| Клиент | Транспорт | Формат данных | Особые гарантии |
| --- | --- | --- | --- |
| Redis Client | TCP (TLS) | Stream/Hash/String/Set | TTL управление, pub/sub, транзакции для идемпотентности |
| MongoDB Client | SRV + TLS | BSON документы | Индексы по agent/user, шардирование, транзакции |
| Qdrant Client | HTTP/gRPC | Векторы + payload JSON | Коллекции с фильтрами, согласованность топ-k |
| PostgreSQL Client | TLS | Таблицы (idempotency, аудит) | ACID, миграции, хранимые TTL |

Каждый доменный сервис получает фабрику клиентов через DI и не знает о конкретных адресах/секретах (их поставляет конфигурационный слой).

## 6. Обязанности на границах

- **API ↔ Business**: API гарантирует версию и схему, бизнес — кросс-сервисные правила и идемпотентность.
- **Business ↔ Domain**: Передаются чистые команды, без сетевых деталей. Domain может предполагать, что идентификаторы/доступ уже проверены.
- **Domain ↔ Storage**: Domain формирует DTO storage-клиента (например, `EpisodeDocument`, `KnowledgePayload`). Storage гарантирует запись, индексацию, health-checkи.
- **Observability Contracts**: Каждый слой обязан логировать trace-id, agent_id, operation_name и latency, что обеспечивает end-to-end трассировку.

## 7. Использование контракта в потоке

Пример: создание эпизода.

1. Клиент → `POST /episodes` с `UniversalEpisodeWriteRequest`.
2. API парсит → передаёт в RequestValidator.
3. RequestValidator создаёт `CreateEpisodeCommand`, проставляет `idempotency_key`.
4. IdempotencyGuard проверяет кэш → при успехе вызывает `EpisodicMemoryService.create_episode`.
5. Сервис пишет документ в Mongo, вектор в Qdrant (через storage-клиенты).
6. Ответ сериализуется в `UniversalWriteResponse` и возвращается вверх.

Аналогичные шаги выполняются для создания знания, процедуры, факта и т.д., что обеспечивает предсказуемость контрактов между слоями.

