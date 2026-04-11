# VK CRM Pro

Готовая CRM-система на **FastAPI + SQLAlchemy + Jinja2** для работы с несколькими VK-аккаунтами в одном интерфейсе.

## Стек
- Backend: FastAPI, SQLAlchemy ORM, Session auth
- DB: SQLite по умолчанию (легко переключается на PostgreSQL через `DATABASE_URL`)
- Frontend: Jinja2 + HTML + CSS + JS

## Возможности
- Авторизация по логину/паролю
- Роли: `admin`, `manager`
- Страницы: Dashboard, VK аккаунты, Сообщения, Клиенты, Логи, Настройки, Пользователи
- CRUD для VK аккаунтов и клиентов
- Единая таблица сообщений по всем аккаунтам + фильтрация/поиск
- Логи действий пользователей
- Сервисный слой для интеграции с VK API (`app/services/vk_service.py`)

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Откройте: `http://127.0.0.1:8000`

## Данные доступа
- login: `admin`
- password: `admin123`

## Переключение на PostgreSQL
В `.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/vk_crm
```

## Где расширять VK интеграцию
- `app/services/vk_service.py`
  - `validate_connection` — проверка токена и long poll
  - `sync_messages_stub` — заменяется на реальный fetch из VK API
  - `long_poll_config_map` — маппинг параметров группы

## Архитектура
- `app/routes` — маршруты и страницы
- `app/models` — ORM модели
- `app/services` — бизнес-логика и интеграции
- `app/core` — конфиг, база, логирование
- `app/templates` — шаблоны интерфейса
- `app/static` — стили и JS
