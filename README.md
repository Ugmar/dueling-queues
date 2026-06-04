# dueling-queues-DDC
# ⚔️ Dueling Queues Bot

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.17-orange?logo=telegram&logoColor=white)](https://github.com/aiogram/aiogram)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker&logoColor=white)](https://www.docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-DeepSeek--V3-black?logo=ollama&logoColor=white)](https://ollama.com)

**Dueling Queues** — это продвинутый Telegram-бот для управления студенческими очередями с игровыми механиками (квизами) и автоматической генерацией вопросов с помощью локальных и облачных нейросетей (LLM).

---

## 🚀 Основные фичи

* **Умное управление очередями**: Студенты могут записываться в очереди по предметам внутри своих академических групп.
* **ИИ-Генератор Квизов**: Администраторы могут загрузить **PDF-файл**, отправить **ссылку на статью** или просто **текст**, а встроенный LLM-движок автоматически сформирует структурированный тест на русском языке.
* **Динамический Скоринг**: За правильные ответы в квизах студенты получают баллы, которые автоматически перестраивают их позиции в очереди.
* **Архитектура контроля (Quiz Guard)**: Специальные middleware блокируют случайные действия пользователя во время прохождения теста.
* **Полная Docker-интеграция**: Быстрое развертывание приложения и базы данных PostgreSQL в один клик.

---

## 🛠 Технологический стек

Проект построен на базе современных асинхронных библиотек и инструментов:

| Технология | Назначение |
| :--- | :--- |
| **Python 3.11-slim** | Базовая среда выполнения (минимизированный Docker-образ) |
| **Aiogram v3.17** | Асинхронный фреймворк для разработки Telegram-ботов |
| **SQLAlchemy v2.0 & Asyncpg** | ОРМ нового поколения с поддержкой полностью асинхронных запросов к БД |
| **PostgreSQL 14** | Реляционная база данных для хранения информации о пользователях, очередях и квизах |
| **Ollama Python API** | Интеграция с языковой моделью `deepseek-v3.1:671b-cloud` для генерации тестов |
| **Trafilatura & PyMuPDF** | Парсинг и извлечение чистого текста из Web-страниц (URL) и документов PDF |
| **Faker** | Генерация реалистичных тестовых данных для наполнения БД (`fill_db.py`) |
| **Autopep8 & Git Hooks** | Автоматическое форматирование кода по стандарту PEP8 перед каждым коммитом |

---

## 📂 Архитектура проекта

Проект спроектирован с разделением ответственности (Слоистые стейт-машины, роутеры и ORM-запросы):

```text
dueling-queues/
├── app/
│   ├── LLM/            # Модуль интеграции с ИИ (промпты, валидация Pydantic, парсинг PDF/URL)
│   ├── database/       # Слой работы с данными (модели SQLAlchemy, асинхронный движок, CRUD)
│   ├── fsm/            # Машины состояний (FSM) по логическим блокам (add, queue, quiz, reg)
│   ├── handlers/       # Общие обработчики команд
│   ├── keyboards/      # Динамические инлайн-клавиатуры
│   ├── middlewares/    # Слой перехвата (сессии БД, защита от спама во время квизов)
│   └── resources/      # Статические тексты и шаблоны сообщений
├── Dockerfile          # Сборка контейнера приложения
├── docker-compose.yml  # Оркестрация контейнеров (App + PostgreSQL)
├── Makefile            # Удобные алиасы для автоматизации разработки
└── main.py             # Точка входа приложения

# Let everything go
make

text
**make** will set up all requirements for proper bot execution. If all keys and paths are valid **make** will run the bot.

# Just preparing development environment
make setup

text
**make** will set up all requirements for proper bot execution.

# Launch
make run

text
**make** will run the bot. (oh, so surprising!)

# Tidy up
make purge

text
**make** will remove virtual environment and cached data.

# Settings
Don't forget to add your **TOKEN** and **DB_URL** in .env file for bot execution.

## Основные команды

- **`make all`** или **`make`** - Запуск всего стека в Docker (по умолчанию)
- **`make run`** - Синоним для `docker-run` (приложение + БД)
- **`make setup`** - Настройка окружения (.env + git hooks)
- **`make reload`** - Полная перезагрузка (down + run)
- **`make purge`** - Полная очистка (Python cache + Docker volumes)

## Docker команды

### Приложение + БД
make docker-run # Запуск/пересборка в фоне
make docker-stop # Остановка (сохраняет volumes)
make docker-down # Полная остановка (удаляет контейнеры)
make docker-logs # Логи приложения в реальном времени

text

### Только БД (queue_postgres)
make db_run # Запуск/пересборка БД
make db_start # Запуск существующей БД
make db_stop # Остановка БД (сохраняет данные)
make db_down # Удаление БД + volume (данные потеряны!)
make db_clear # Быстрое пересоздание чистой БД

text

## Очистка
make clean # Только Python cache (*.pyc, pycache)
make purge # Полная очистка (clean + docker down -v)

text

## Git Hooks
make git-hooks-setup # Настройка pre-commit хуков (.githooks)

text

## ⚠️ ВНИМАНИЕ
- **`db_down`** удаляет все данные БД!
- Не забудьте настроить `.env` с вашими `TOKEN` и `DB_URL`
