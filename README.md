# dueling-queues-DDC
Fan project =)

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
