# 🚀 Быстрый старт: OpenAI Memory Demo

Простая инструкция для запуска демонстрационного ноутбука.

## 1️⃣ Запустите сервисы (5 минут)

```bash
# В корне проекта
cd /Users/dsh/memory-agents
docker-compose up -d
```

Проверьте, что все сервисы запущены:
```bash
docker ps
# Должны быть: redis, mongodb, qdrant, postgres
```

## 2️⃣ Установите зависимости (2 минуты)

```bash
cd examples/notebooks
pip install -r requirements-openai-demo.txt
```

## 3️⃣ Настройте OpenAI API (1 минута)

Создайте файл `.env` в корне проекта:
```bash
# В корне проекта
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

Или отредактируйте существующий `.env` и добавьте строку:
```
OPENAI_API_KEY=sk-proj-...
```

Получить ключ: https://platform.openai.com/api-keys

## 4️⃣ Запустите ноутбук (1 минута)

```bash
cd examples/notebooks
jupyter notebook openai_memory_demo.ipynb
```

Или в VS Code: просто откройте файл `openai_memory_demo.ipynb`

## 5️⃣ Запустите все ячейки

В Jupyter:
- Меню: **Cell** → **Run All**

В VS Code:
- Кнопка **Run All** вверху ноутбука

## ✨ Готово!

Вы увидите:
- ✅ Подключение к OpenAI API
- ✅ Проверку всех сервисов
- ✅ Демонстрацию Working Memory
- ✅ Демонстрацию Episodic Memory
- ✅ Демонстрацию Semantic Memory
- ✅ Интерактивный чат с LLM
- ✅ Визуализацию всей сохраненной информации

## ⚠️ Устранение проблем

### Сервисы не запускаются
```bash
docker-compose down
docker-compose up -d
docker-compose logs
```

### OpenAI ошибка
- Проверьте `.env` файл
- Проверьте баланс: https://platform.openai.com/account/usage
- Попробуйте новый ключ

### Импорт не работает
```bash
# Переустановите
pip install --upgrade -r requirements-openai-demo.txt
```

## 💰 Стоимость

GPT-4o-mini очень дешевый:
- Весь демо: ~$0.01-0.02 (1-2 цента)
- 1000 запросов: ~$0.50

## 📖 Подробная документация

См. [README_OPENAI_DEMO.md](./README_OPENAI_DEMO.md)

## 🎯 Следующие шаги

После демо попробуйте:
1. Изменить вопросы в ноутбуке
2. Добавить свои сценарии
3. Изучить другие примеры в `/examples`
4. Интегрировать в свой проект

---

**Время от установки до запуска: ~10 минут** ⏱️

