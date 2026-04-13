from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.client import Client
from app.models.log_entry import LogEntry
from app.models.message import Message
from app.models.setting import Setting
from app.models.user import User
from app.models.vk_account import VKAccount
from app.routes.deps import get_current_user, require_admin
from app.services.dashboard_service import get_dashboard_stats
from app.services.log_service import write_log
from app.services.vk_service import VKService

router = APIRouter()
templates = Jinja2Templates(directory='app/templates')
templates.env.globals['static_asset_version'] = settings.static_asset_version


@router.get('/dashboard')
def dashboard(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stats = get_dashboard_stats(db)
    return templates.TemplateResponse('dashboard.html', {'request': request, 'stats': stats, 'current_user': current_user})


@router.get('/accounts')
def accounts_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    accounts = db.query(VKAccount).order_by(VKAccount.created_at.desc()).all()
    return templates.TemplateResponse('accounts.html', {'request': request, 'accounts': accounts, 'current_user': current_user})


@router.post('/accounts/create')
def create_account(
    request: Request,
    name: str = Form(...),
    group_id: str = Form(...),
    status: str = Form('active'),
    access_token: str = Form(''),
    long_poll_server: str = Form(''),
    long_poll_key: str = Form(''),
    long_poll_ts: str = Form(''),
    description: str = Form(''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(VKAccount).count() >= 1:
        write_log(db, action='VK_ACCOUNT_CREATE_BLOCKED', details='Разрешен только один личный VK аккаунт', level='WARNING', user_id=current_user.id)
        return RedirectResponse('/accounts', status_code=303)

    account = VKAccount(
        name=name,
        group_id=group_id,
        status=status,
        access_token=access_token,
        long_poll_server=long_poll_server,
        long_poll_key=long_poll_key,
        long_poll_ts=long_poll_ts,
        description=description,
        owner_id=current_user.id,
    )
    db.add(account)
    db.commit()
    write_log(db, action='VK_ACCOUNT_CREATE', details=f'Создан VK аккаунт {name}', user_id=current_user.id)
    return RedirectResponse('/accounts', status_code=303)


@router.post('/accounts/{account_id}/verify')
def verify_account_token(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(VKAccount).filter(VKAccount.id == account_id).first()
    if not account:
        return RedirectResponse('/accounts', status_code=303)

    vk_service = VKService(db)
    is_ok, status_text = vk_service.validate_connection(account)
    account.status = 'active' if is_ok else 'error'
    log_action = 'VK_TOKEN_VERIFY' if is_ok else 'VK_TOKEN_VERIFY_ERROR'
    log_level = 'INFO' if is_ok else 'ERROR'
    write_log(db, action=log_action, details=f'{account.name}: {status_text}', level=log_level, user_id=current_user.id)
    db.commit()
    return RedirectResponse('/accounts', status_code=303)


@router.post('/accounts/{account_id}/update')
def update_account(
    account_id: int,
    name: str = Form(...),
    group_id: str = Form(...),
    status: str = Form('active'),
    access_token: str = Form(''),
    long_poll_server: str = Form(''),
    long_poll_key: str = Form(''),
    long_poll_ts: str = Form(''),
    description: str = Form(''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(VKAccount).filter(VKAccount.id == account_id).first()
    if not account:
        return RedirectResponse('/accounts', status_code=303)
    account.name = name
    account.group_id = group_id
    account.status = status
    account.access_token = access_token
    account.long_poll_server = long_poll_server
    account.long_poll_key = long_poll_key
    account.long_poll_ts = long_poll_ts
    account.description = description
    db.commit()
    write_log(db, action='VK_ACCOUNT_UPDATE', details=f'Обновлен VK аккаунт {name}', user_id=current_user.id)
    return RedirectResponse('/accounts', status_code=303)


@router.post('/accounts/{account_id}/delete')
def delete_account(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    account = db.query(VKAccount).filter(VKAccount.id == account_id).first()
    if account:
        db.delete(account)
        db.commit()
        write_log(db, action='VK_ACCOUNT_DELETE', details=f'Удален VK аккаунт #{account_id}', user_id=current_user.id)
    return RedirectResponse('/accounts', status_code=303)


@router.post('/accounts/{account_id}/sync')
def sync_account(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(VKAccount).filter(VKAccount.id == account_id).first()
    if account:
        vk_service = VKService(db)
        is_ok, status_text = vk_service.validate_connection(account)
        if is_ok:
            sync_ok, _, sync_text = vk_service.sync_dialogs(account)
            account.status = 'active' if sync_ok else 'error'
            if sync_ok:
                write_log(
                    db,
                    action='VK_SYNC',
                    details=f'{account.name}: {sync_text}',
                    user_id=current_user.id,
                )
            else:
                write_log(
                    db,
                    action='VK_SYNC_ERROR',
                    details=f'{account.name}: {sync_text}',
                    level='ERROR',
                    user_id=current_user.id,
                )
        else:
            account.status = 'error'
            write_log(db, action='VK_SYNC_ERROR', details=f'{account.name}: {status_text}', level='ERROR', user_id=current_user.id)
        db.commit()
    return RedirectResponse('/accounts', status_code=303)


@router.get('/messages')
def messages_page(
    request: Request,
    account_id: int | None = Query(default=None),
    q: str = Query(default=''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Message).order_by(Message.sent_at.desc())
    if account_id:
        query = query.filter(Message.vk_account_id == account_id)
    if q:
        query = query.filter(Message.text.ilike(f'%{q}%'))
    messages = query.limit(300).all()
    accounts = db.query(VKAccount).order_by(VKAccount.name.asc()).all()
    return templates.TemplateResponse(
        'messages.html',
        {'request': request, 'messages': messages, 'accounts': accounts, 'account_id': account_id, 'q': q, 'current_user': current_user},
    )


@router.post('/messages/{message_id}/toggle-read')
def toggle_message_read(message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if msg:
        msg.is_read = not msg.is_read
        db.commit()
        write_log(db, action='MESSAGE_STATUS', details=f'Message {message_id} read={msg.is_read}', user_id=current_user.id)
    return RedirectResponse('/messages', status_code=303)


@router.get('/clients')
def clients_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clients = db.query(Client).order_by(Client.created_at.desc()).all()
    managers = db.query(User).filter(User.is_active.is_(True)).order_by(User.full_name.asc()).all()
    return templates.TemplateResponse('clients.html', {'request': request, 'clients': clients, 'managers': managers, 'current_user': current_user})


@router.post('/clients/create')
def create_client(
    full_name: str = Form(...),
    vk_link: str = Form(...),
    vk_user_id: str = Form(''),
    tags: str = Form(''),
    status: str = Form('new'),
    notes: str = Form(''),
    manager_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = Client(
        full_name=full_name,
        vk_link=vk_link,
        vk_user_id=vk_user_id,
        tags=tags,
        status=status,
        notes=notes,
        manager_id=manager_id,
    )
    db.add(client)
    db.commit()
    write_log(db, action='CLIENT_CREATE', details=f'Создан клиент {full_name}', user_id=current_user.id)
    return RedirectResponse('/clients', status_code=303)


@router.post('/clients/{client_id}/delete')
def delete_client(client_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if client:
        db.delete(client)
        db.commit()
        write_log(db, action='CLIENT_DELETE', details=f'Удален клиент #{client_id}', user_id=current_user.id)
    return RedirectResponse('/clients', status_code=303)


@router.get('/users')
def users_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse('users.html', {'request': request, 'users': users, 'current_user': current_user})


@router.post('/users/create')
def create_user(
    username: str = Form(...),
    full_name: str = Form(...),
    role: str = Form('manager'),
    password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from app.services.auth_service import hash_password

    exists = db.query(User).filter(or_(User.username == username, User.full_name == full_name)).first()
    if exists:
        return RedirectResponse('/users', status_code=303)

    user = User(username=username, full_name=full_name, role=role, password_hash=hash_password(password), is_active=True)
    db.add(user)
    db.commit()
    write_log(db, action='USER_CREATE', details=f'Создан пользователь {username}', user_id=current_user.id)
    return RedirectResponse('/users', status_code=303)


@router.get('/logs')
def logs_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(LogEntry).order_by(LogEntry.created_at.desc()).limit(500).all()
    return templates.TemplateResponse('logs.html', {'request': request, 'logs': logs, 'current_user': current_user})


@router.get('/settings')
def settings_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = db.query(Setting).order_by(Setting.group_name.asc(), Setting.key.asc()).all()
    return templates.TemplateResponse('settings.html', {'request': request, 'settings': settings, 'current_user': current_user})


@router.post('/settings/save')
def save_setting(
    key: str = Form(...),
    value: str = Form(''),
    group_name: str = Form('system'),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(Setting).filter(Setting.key == key).first()
    if item:
        item.value = value
        item.group_name = group_name
    else:
        item = Setting(key=key, value=value, group_name=group_name)
        db.add(item)
    db.commit()
    write_log(db, action='SETTING_SAVE', details=f'Сохранен параметр {key}', user_id=current_user.id)
    return RedirectResponse('/settings', status_code=303)
