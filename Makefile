# ==================== КОНСТАНТЫ ====================
# Основные константы проекта
MAIN = main.py              # Главный файл приложения
FILL_DB = app/database/fill_db.py# Файл инициализации БД
CLEAR_DB = app/database/clear_db.py # Файл очистки БД (кроме admins)
DC = docker-compose.yml     # Файл конфигурации Docker Compose

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================
# Основные команды, которые будут использоваться чаще всего

# Цель по умолчанию - запускается при вызове 'make' без аргументов
# Зависит от docker-run, то есть запустит весь стек в Docker
.PHONY: all
all: docker-run

# Команда 'make run' - синоним для docker-run
# Запускает приложение и БД в контейнерах
.PHONY: run
run: docker-run

# Настройка окружения перед первым запуском:
# 1. Создает .env файл из шаблона (если его нет)
# 2. Настраивает git hooks для пре-коммит проверок
.PHONY: setup
setup: .env git-hooks-setup
	@echo "Настройка окружения завершена (только .env и git hooks)"

# Полная перезагрузка проекта:
# 1. Останавливает и удаляет контейнеры
# 2. Запускает все заново
.PHONY: reload
reload: docker-down docker-run

# ==================== ENV ФАЙЛ ====================
# Автоматическое создание .env файла из шаблона при первом запуске
# Если файла .env нет, но есть .env.sample - копируем шаблон
.env:
	@if [ ! -f .env ] && [ -f .env.sample ]; then \
		echo "Copying .env file (You need to initialise it manually)..."; \
		cp .env.sample .env; \
	fi

# ==================== GIT HOOKS ====================
# Настройка git hooks для автоматических проверок кода
# Git hooks находятся в папке .githooks и будут выполняться автоматически
.PHONY: git-hooks-setup
git-hooks-setup:
	@echo "Setting up githooks..."
	@git config core.hooksPath .githooks

# ==================== ОЧИСТКА ====================
# Удаление временных файлов Python:
# - *.pyc - скомпилированные байт-код файлы
# - __pycache__ - кэш-директории Python 3
.PHONY: clean
clean:
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Полная очистка проекта:
# 1. Удаляет временные файлы Python (вызывает clean)
# 2. Останавливает и удаляет Docker контейнеры и volumes
.PHONY: purge
purge:
	@echo "Полная очистка..."
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	docker-compose -f $(DC) down -v 2>/dev/null || true

# ==================== DOCKER - ПРИЛОЖЕНИЕ ====================
# Запуск всего стека (приложение + БД) в Docker
# Флаг --build пересобирает образы при необходимости
# Флаг -d запускает контейнеры в фоновом режиме (detached mode)
.PHONY: docker-run
docker-run:
	docker-compose -f $(DC) up --build -d

# Остановка контейнеров без удаления
# Контейнеры можно будет запустить снова командой docker-start
.PHONY: docker-stop
docker-stop:
	docker-compose -f $(DC) stop

# Полная остановка и удаление контейнеров
# Удаляет контейнеры, но сохраняет volumes (данные БД)
.PHONY: docker-down
docker-down:
	docker-compose -f $(DC) down

# Просмотр логов приложения в реальном времени
# Флаг -f (follow) позволяет видеть новые логи по мере их появления
.PHONY: docker-logs
docker-logs:
	docker-compose -f $(DC) logs -f app

# ==================== DOCKER - БАЗА ДАННЫХ ====================
# Запуск только базы данных (без приложения)
# Полезно для разработки, когда нужно работать только с БД
.PHONY: db_run
db_run:
	docker-compose -f $(DC) up --build queue_postgres -d

# Запуск уже созданной БД (если контейнер был остановлен)
# Не пересобирает образ, просто запускает существующий контейнер
.PHONY: db_start
db_start:
	docker-compose -f $(DC) start queue_postgres

# Остановка контейнера с БД без удаления
# Данные сохраняются в volume
.PHONY: db_stop
db_stop:
	docker-compose -f $(DC) stop queue_postgres

# Полная остановка и удаление контейнера БД с удалением volume
# Флаг -v удаляет все связанные volumes (ВНИМАНИЕ: данные будут потеряны!)
.PHONY: db_down
db_down:
	docker-compose -f $(DC) down -v queue_postgres

# Заполнение базы данных тестовыми данными
# Выполняется внутри контейнера приложения, поэтому приложение должно быть запущено
.PHONY: fill_db
fill_db:
	docker-compose -f $(DC) run --rm app python3 $(FILL_DB) 100

# Быстрое пересоздание БД:
# 1. Удаляет контейнер БД и данные (db_down)
# 2. Запускает чистую БД (db_run)
.PHONY: db_clear
db_clear: db_down db_run

# Очистить все таблицы (кроме admins) внутри контейнера приложения
.PHONY: clear_db
clear_db:
	docker-compose -f $(DC) run --rm --build app python3 $(CLEAR_DB)

# Объявляем все цели как .PHONY, чтобы Make не путал их с файлами
# Это стандартная практика для целей, которые не создают файлов с таким же именем
.PHONY: all run setup reload git-hooks-setup clean purge
.PHONY: docker-run docker-stop docker-down docker-logs
.PHONY: db_run db_start db_stop db_down fill_db db_clear
.PHONY: clear_db
