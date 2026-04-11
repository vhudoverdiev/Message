# VK CRM Pro (Starter Pro)
Расширенный локальный CRM starter на FastAPI + SQLite.

## Возможности
- Авторизация (admin/admin)
- Роли (admin / manager)
- Dashboard
- CRUD заготовки: VK аккаунты, клиенты
- Сообщения (единый inbox)
- Логи
- Настройки
- Сервисный слой для VK API

## Запуск
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Открыть: http://127.0.0.1:8000
