# Omni-Channel CRM (Gmail + Telegram + VK)

Production-ready foundation CRM на **FastAPI + SQLAlchemy + Jinja2** с модульной архитектурой каналов.

## Что реализовано
- Отдельные вкладки: **Gmail**, **Telegram**, **VK Hub**.
- Подключение каналов через безопасное хранение токенов в БД (шифрование на основе `SECRET_KEY`).
- Синхронизация входящих данных:
  - Gmail: список писем, отправитель, тема, дата, read/unread, просмотр полного текста, поиск/refresh.
  - Telegram (Bot API): входящие уведомления, отправитель, текст, дата, статус обработки.
  - VK Community: список диалогов/сообщений, статусы (new/in_progress/processed), ответ в диалог из CRM.
- Логирование всех действий и ошибок синхронизации.
- Модульная база для расширения каналов (WhatsApp/Instagram/Avito и т.д.).

## Рекомендуемый стек и почему
- **FastAPI** — быстрый API/web слой, удобен для async-интеграций и микросервисного роста.
- **SQLAlchemy 2.x** — строгая ORM-модель, миграционный путь к PostgreSQL.
- **Jinja2 + server-side rendering** — простой и надежный admin UI без перегрузки фронтендом.
- **SQLite (dev) / PostgreSQL (prod)** — быстрый старт + готовый путь к production.
- **.env + SECRET_KEY** — централизованная конфигурация и защита секретов.

## Архитектура
- `app/routes` — HTTP-роуты и UI endpoints.
- `app/services/channel_service.py` — бизнес-логика интеграции каналов (Gmail/Telegram/VK).
- `app/models/channel_account.py` — подключенные каналы и токены.
- `app/models/channel_message.py` — унифицированное хранилище сообщений каналов.
- `app/core/security.py` — шифрование/дешифрование токенов.

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Откройте: `http://127.0.0.1:8000`

## Настройки .env
```env
APP_NAME=Omni-Channel CRM
SECRET_KEY=change_me_to_long_random_value
DATABASE_URL=sqlite:///./crm.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## Подключение каналов
1. Войдите как администратор.
2. Перейдите на вкладки `Gmail`, `Telegram`, `VK Hub`.
3. Укажите токены интеграций и выполните синхронизацию.

> В этой версии Gmail использует уже полученный OAuth Access Token, Telegram — Bot Token, VK — API token сообщества.
