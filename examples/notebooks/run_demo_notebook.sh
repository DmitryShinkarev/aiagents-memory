#!/bin/bash

# Скрипт для запуска демонстрационного Jupyter Notebook
# Memory Agents Demo

set -e  # Exit on error

echo "🚀 Memory Agents - Запуск демонстрационного ноутбука"
echo "=================================================="
echo ""

# Проверка наличия виртуального окружения
if [ ! -d "venv_demo" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "Создаю виртуальное окружение venv_demo..."
    python3 -m venv venv_demo
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv_demo/bin/activate

# Проверка и установка зависимостей
echo "📦 Проверка зависимостей..."
if ! python -c "import jupyter" &> /dev/null; then
    echo "📥 Установка Jupyter и зависимостей..."
    pip install --upgrade pip setuptools wheel
    pip install jupyter ipykernel notebook ipywidgets
fi

# Регистрация kernel для Jupyter
echo "🔌 Регистрация Python kernel для Jupyter..."
python -m ipykernel install --user --name=memory-agents-demo --display-name="Memory Agents Demo"

# Проверка наличия ноутбука
if [ ! -f "demo_memory_agents.ipynb" ]; then
    echo "❌ Файл demo_memory_agents.ipynb не найден!"
    exit 1
fi

# Проверка Docker сервисов
echo ""
echo "🐳 Проверка Docker сервисов..."
echo "=================================================="

if ! docker ps &> /dev/null; then
    echo "⚠️  Docker не запущен или недоступен"
    echo "Пожалуйста, запустите Docker и затем выполните:"
    echo "  docker compose up -d"
    echo ""
else
    # Проверка статуса контейнеров
    RUNNING=$(docker compose ps --services --filter "status=running" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$RUNNING" -lt 4 ]; then
        echo "⚠️  Некоторые сервисы не запущены"
        echo "Запускаю Docker Compose сервисы..."
        docker compose up -d

        echo "⏳ Ожидание инициализации сервисов (10 секунд)..."
        sleep 10
    else
        echo "✅ Все Docker сервисы запущены:"
        docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
    fi
fi

echo ""
echo "=================================================="
echo "✅ Все готово к запуску!"
echo "=================================================="
echo ""
echo "📓 Запускаю Jupyter Notebook..."
echo ""
echo "После открытия браузера:"
echo "  1. Откройте файл: demo_memory_agents.ipynb"
echo "  2. Выберите kernel: Memory Agents Demo"
echo "  3. Выполните: Cell → Run All"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Запуск Jupyter Notebook
jupyter notebook demo_memory_agents.ipynb

# Деактивация при выходе
deactivate
