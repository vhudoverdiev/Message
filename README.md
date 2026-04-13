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
- Этап 15: ручное подключение **1 личного VK аккаунта** через user token

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Альтернатива (теперь поддерживается):
```bash
python run.py
```

Откройте: `http://127.0.0.1:8000`

## Почему не запускается (`python run.py`)
Если видите ошибку `can't open file ... run.py: [Errno 2] No such file or directory`, значит в проекте не было `run.py`.

Теперь доступны оба варианта запуска:
1. `python run.py`
2. `uvicorn app.main:app --reload`

Для Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

## Данные доступа
- login: `admin`
- password: `admin123`

## Переключение на PostgreSQL
В `.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/vk_crm
STATIC_ASSET_VERSION=1
```

Если после деплоя вы видите старые стили/JS, увеличьте `STATIC_ASSET_VERSION` (например, `2`) и перезапустите сервис — это принудительно обновит кэш статических файлов в браузере.

## Этап 15: как подключить личный аккаунт (manual user token)
1. Войдите в CRM под `admin`.
2. Откройте страницу **VK аккаунты**.
3. Добавьте один аккаунт и вставьте `user token` вручную.
4. Нажмите **Проверить токен** (вызов `users.get`).
5. Нажмите **Синхро диалогов** (вызов `messages.getConversations`).

> В этой схеме VK ID OAuth не используется.

## Где расширять VK интеграцию
- `app/services/vk_service.py`
  - `validate_connection` — проверка user token через VK API
  - `sync_dialogs` — синхронизация диалогов личного аккаунта
  - `long_poll_config_map` — маппинг параметров группы

## Архитектура
- `app/routes` — маршруты и страницы
- `app/models` — ORM модели
- `app/services` — бизнес-логика и интеграции
- `app/core` — конфиг, база, логирование
- `app/templates` — шаблоны интерфейса
- `app/static` — стили и JS
