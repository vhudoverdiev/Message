from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.client import Client
from app.models.message import Message
from app.models.log_entry import LogEntry
from app.models.setting import Setting
from app.models.user import User
from app.models.channel_account import ChannelAccount
from app.models.channel_message import ChannelMessage
from app.routes.deps import get_current_user, require_admin
from app.services.dashboard_service import get_dashboard_stats
from app.services.log_service import write_log
from app.services.channel_service import ChannelService

router = APIRouter()
templates = Jinja2Templates(directory='app/templates')
templates.env.globals['static_asset_version'] = settings.static_asset_version


@router.get('/')
def root():
    return RedirectResponse('/dashboard', status_code=303)


@router.get('/dashboard')
def dashboard(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stats = get_dashboard_stats(db)
    return templates.TemplateResponse('dashboard.html', {'request': request, 'stats': stats, 'current_user': current_user})


@router.get('/accounts')
def accounts_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    accounts = ChannelService(db).list_accounts('vk')
    return templates.TemplateResponse('accounts.html', {'request': request, 'accounts': accounts, 'current_user': current_user})


@router.post('/accounts/create')
def create_account(
    request: Request,
    name: str = Form(...),
    group_id: str = Form(...),
    access_token: str = Form(''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChannelService(db)
    account = service.create_vk_account(name=name, group_id=group_id, access_token=access_token)
    write_log(db, action='VK_COMMUNITY_CREATE', details=f'Создано VK сообщество {account.name}', user_id=current_user.id)
    return RedirectResponse('/accounts', status_code=303)


@router.post('/accounts/{account_id}/verify')
def verify_account_token(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(ChannelAccount).filter(ChannelAccount.id == account_id, ChannelAccount.channel == 'vk').first()
    if not account:
        return RedirectResponse('/accounts', status_code=303)

    is_ok, status_text = ChannelService(db).verify_vk_account(account)
    log_action = 'VK_COMMUNITY_VERIFY' if is_ok else 'VK_COMMUNITY_VERIFY_ERROR'
    log_level = 'INFO' if is_ok else 'ERROR'
    write_log(db, action=log_action, details=f'{account.name}: {status_text}', level=log_level, user_id=current_user.id)
    return RedirectResponse('/accounts', status_code=303)


@router.post('/accounts/{account_id}/update')
def update_account(
    account_id: int,
    name: str = Form(...),
    group_id: str = Form(...),
    access_token: str = Form(''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(ChannelAccount).filter(ChannelAccount.id == account_id, ChannelAccount.channel == 'vk').first()
    if not account:
        return RedirectResponse('/accounts', status_code=303)
    ChannelService(db).update_vk_account(account, name=name, group_id=group_id, access_token=access_token)
    write_log(db, action='VK_COMMUNITY_UPDATE', details=f'Обновлено VK сообщество {name}', user_id=current_user.id)
    return RedirectResponse('/accounts', status_code=303)


@router.post('/accounts/{account_id}/delete')
def delete_account(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    account = db.query(ChannelAccount).filter(ChannelAccount.id == account_id, ChannelAccount.channel == 'vk').first()
    if account:
        ChannelService(db).delete_vk_account(account)
        write_log(db, action='VK_COMMUNITY_DELETE', details=f'Удалено VK сообщество #{account_id}', user_id=current_user.id)
    return RedirectResponse('/accounts', status_code=303)


@router.post('/accounts/{account_id}/sync')
def sync_account(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(ChannelAccount).filter(ChannelAccount.id == account_id, ChannelAccount.channel == 'vk').first()
    if account:
        ok, details = ChannelService(db).sync_vk_account(account)
        write_log(
            db,
            action='VK_COMMUNITY_SYNC' if ok else 'VK_COMMUNITY_SYNC_ERROR',
            details=f'{account.name}: {details}',
            level='INFO' if ok else 'ERROR',
            user_id=current_user.id,
        )
    return RedirectResponse('/accounts', status_code=303)


@router.get('/messages')
def messages_page(
    request: Request,
    account_id: int | None = Query(default=None),
    q: str = Query(default=''),
    priority: str = Query(default=''),
    sla_only: str = Query(default='0'),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ChannelMessage).filter(ChannelMessage.channel == 'vk').order_by(ChannelMessage.created_at.desc())
    if account_id:
        query = query.filter(ChannelMessage.account_id == account_id)
    if q:
        query = query.filter(or_(ChannelMessage.body_preview.ilike(f'%{q}%'), ChannelMessage.sender_name.ilike(f'%{q}%')))
    messages = query.limit(500).all()

    now = datetime.utcnow()
    enriched_messages = []
    for message in messages:
        message_priority = ChannelService.classify_vk_priority(message.body_preview)
        is_sla_risk = (not message.is_read) and ((now - message.created_at) > timedelta(hours=2))
        if priority and message_priority != priority:
            continue
        if sla_only == '1' and not is_sla_risk:
            continue
        enriched_messages.append({
            'item': message,
            'priority': message_priority,
            'is_sla_risk': is_sla_risk,
        })

    base_query = db.query(ChannelMessage).filter(ChannelMessage.channel == 'vk')
    if account_id:
        base_query = base_query.filter(ChannelMessage.account_id == account_id)
    unread_count = base_query.filter(ChannelMessage.is_read.is_(False)).count()
    total_count = base_query.count()
    high_priority_count = sum(1 for row in enriched_messages if row['priority'] == 'high')
    sla_risk_count = sum(1 for row in enriched_messages if row['is_sla_risk'])
    accounts = db.query(ChannelAccount).filter(ChannelAccount.channel == 'vk').order_by(ChannelAccount.name.asc()).all()
    return templates.TemplateResponse(
        'messages.html',
        {
            'request': request,
            'messages': enriched_messages,
            'accounts': accounts,
            'account_id': account_id,
            'q': q,
            'priority': priority,
            'sla_only': sla_only,
            'unread_count': unread_count,
            'total_count': total_count,
            'high_priority_count': high_priority_count,
            'sla_risk_count': sla_risk_count,
            'current_user': current_user,
        },
    )


@router.post('/messages/{message_id}/toggle-read')
def toggle_message_read(message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = db.query(ChannelMessage).filter(ChannelMessage.id == message_id, ChannelMessage.channel == 'vk').first()
    if msg:
        msg.is_read = not msg.is_read
        msg.status = 'processed' if msg.is_read else 'new'
        db.commit()
        write_log(db, action='VK_MESSAGE_STATUS', details=f'VK Message {message_id} read={msg.is_read}', user_id=current_user.id)
    return RedirectResponse('/messages', status_code=303)


@router.post('/messages/{message_id}/reply')
def reply_to_message(
    message_id: int,
    reply_text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = db.query(ChannelMessage).filter(ChannelMessage.id == message_id, ChannelMessage.channel == 'vk').first()
    if not msg:
        return RedirectResponse('/messages', status_code=303)

    account = db.query(ChannelAccount).filter(ChannelAccount.id == msg.account_id, ChannelAccount.channel == 'vk').first()
    if not account:
        write_log(
            db,
            action='VK_MESSAGE_REPLY_ERROR',
            details=f'Не найден VK аккаунт для сообщения #{message_id}',
            level='ERROR',
            user_id=current_user.id,
        )
        return RedirectResponse('/messages', status_code=303)

    ok, details = ChannelService(db).send_vk_reply(account, peer_id=msg.conversation_id, message=reply_text)
    write_log(
        db,
        action='VK_MESSAGE_REPLY' if ok else 'VK_MESSAGE_REPLY_ERROR',
        details=f'Сообщение #{message_id}: {details}',
        level='INFO' if ok else 'ERROR',
        user_id=current_user.id,
    )
    if ok:
        msg.status = 'processed'
        msg.is_read = True
        db.commit()
    return RedirectResponse('/messages', status_code=303)


@router.get('/clients')
def clients_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clients = db.query(Client).order_by(Client.created_at.desc()).all()
    managers = db.query(User).filter(User.is_active.is_(True)).order_by(User.full_name.asc()).all()
    return templates.TemplateResponse('clients.html', {'request': request, 'clients': clients, 'managers': managers, 'current_user': current_user})


@router.get('/clients/{client_id}')
def client_profile_page(client_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return RedirectResponse('/clients', status_code=303)

    legacy_messages = db.query(Message).filter(Message.client_id == client.id).order_by(Message.sent_at.desc()).limit(100).all()
    channel_query = db.query(ChannelMessage).filter(ChannelMessage.channel == 'vk')
    if client.vk_user_id:
        channel_query = channel_query.filter(
            or_(
                ChannelMessage.conversation_id.ilike(f'%{client.vk_user_id}%'),
                ChannelMessage.sender_name.ilike(f'%{client.vk_user_id}%'),
            )
        )
    unified_messages = channel_query.order_by(ChannelMessage.created_at.desc()).limit(100).all()

    timeline = [
        {
            'source': 'client',
            'title': 'Карточка создана',
            'body': f'Клиент добавлен в CRM со статусом {client.status}',
            'created_at': client.created_at,
        }
    ]
    for msg in legacy_messages:
        timeline.append({
            'source': 'legacy',
            'title': 'Legacy VK сообщение',
            'body': msg.text,
            'created_at': msg.sent_at,
            'is_read': msg.is_read,
        })
    for msg in unified_messages:
        timeline.append({
            'source': 'unified',
            'title': f'VK Inbox · {msg.sender_name or "Unknown"}',
            'body': msg.body_preview,
            'created_at': msg.created_at,
            'is_read': msg.is_read,
            'priority': ChannelService.classify_vk_priority(msg.body_preview),
            'conversation_id': msg.conversation_id,
        })
    timeline.sort(key=lambda row: row['created_at'], reverse=True)

    return templates.TemplateResponse(
        'client_profile.html',
        {
            'request': request,
            'client': client,
            'timeline': timeline[:200],
            'current_user': current_user,
        },
    )


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


@router.get('/gmail')
def gmail_page(
    request: Request,
    q: str = Query(default=''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChannelService(db)
    accounts = service.list_accounts('gmail')
    account = accounts[0] if accounts else None
    query = db.query(ChannelMessage).filter(ChannelMessage.channel == 'gmail').order_by(ChannelMessage.created_at.desc())
    if account:
        query = query.filter(ChannelMessage.account_id == account.id)
    if q:
        query = query.filter(or_(ChannelMessage.subject.ilike(f'%{q}%'), ChannelMessage.body_preview.ilike(f'%{q}%')))
    messages = query.limit(100).all()
    return templates.TemplateResponse('gmail.html', {'request': request, 'messages': messages, 'account': account, 'q': q, 'current_user': current_user})


@router.post('/gmail/connect')
def gmail_connect(
    name: str = Form(...),
    email: str = Form('me'),
    access_token: str = Form(''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ChannelService(db).upsert_account('gmail', None, name=name, external_id=email, token=access_token)
    write_log(db, action='GMAIL_CONNECT', details=f'Подключен Gmail: {email}', user_id=current_user.id)
    return RedirectResponse('/gmail', status_code=303)


@router.post('/gmail/sync')
def gmail_sync(
    q: str = Form(''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(ChannelAccount).filter(ChannelAccount.channel == 'gmail').order_by(ChannelAccount.created_at.desc()).first()
    if not account:
        return RedirectResponse('/gmail', status_code=303)
    ok, details = ChannelService(db).sync_gmail(account, q)
    write_log(db, action='GMAIL_SYNC' if ok else 'GMAIL_SYNC_ERROR', details=details, level='INFO' if ok else 'ERROR', user_id=current_user.id)
    return RedirectResponse('/gmail', status_code=303)


@router.get('/telegram')
def telegram_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ChannelService(db)
    accounts = service.list_accounts('telegram')
    account = accounts[0] if accounts else None
    query = db.query(ChannelMessage).filter(ChannelMessage.channel == 'telegram').order_by(ChannelMessage.created_at.desc())
    if account:
        query = query.filter(ChannelMessage.account_id == account.id)
    messages = query.limit(150).all()
    return templates.TemplateResponse('telegram.html', {'request': request, 'messages': messages, 'account': account, 'current_user': current_user})


@router.post('/telegram/connect')
def telegram_connect(
    name: str = Form(...),
    bot_username: str = Form(''),
    bot_token: str = Form(''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ChannelService(db).upsert_account('telegram', None, name=name, external_id=bot_username, token=bot_token)
    write_log(db, action='TELEGRAM_CONNECT', details=f'Подключен Telegram bot: {bot_username}', user_id=current_user.id)
    return RedirectResponse('/telegram', status_code=303)


@router.post('/telegram/sync')
def telegram_sync(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(ChannelAccount).filter(ChannelAccount.channel == 'telegram').order_by(ChannelAccount.created_at.desc()).first()
    if not account:
        return RedirectResponse('/telegram', status_code=303)
    ok, details = ChannelService(db).sync_telegram(account)
    write_log(db, action='TELEGRAM_SYNC' if ok else 'TELEGRAM_SYNC_ERROR', details=details, level='INFO' if ok else 'ERROR', user_id=current_user.id)
    return RedirectResponse('/telegram', status_code=303)


@router.post('/telegram/messages/{message_id}/status')
def telegram_mark_status(
    message_id: int,
    status: str = Form('processed'),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = db.query(ChannelMessage).filter(ChannelMessage.id == message_id, ChannelMessage.channel == 'telegram').first()
    if msg:
        msg.status = status
        msg.is_read = status == 'processed'
        db.commit()
        write_log(db, action='TELEGRAM_STATUS', details=f'Message #{message_id} -> {status}', user_id=current_user.id)
    return RedirectResponse('/telegram', status_code=303)


@router.get('/vk-hub')
def vk_hub_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ChannelService(db)
    accounts = service.list_accounts('vk')
    account = accounts[0] if accounts else None
    dialogs = db.query(ChannelMessage).filter(ChannelMessage.channel == 'vk').order_by(ChannelMessage.created_at.desc()).limit(200).all()
    return templates.TemplateResponse('vk_hub.html', {'request': request, 'dialogs': dialogs, 'account': account, 'current_user': current_user})


@router.post('/vk-hub/connect')
def vk_hub_connect(
    name: str = Form(...),
    group_id: str = Form(''),
    access_token: str = Form(''),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ChannelService(db).upsert_account('vk', None, name=name, external_id=group_id, token=access_token)
    write_log(db, action='VK_COMMUNITY_CONNECT', details=f'Подключено VK сообщество: {group_id}', user_id=current_user.id)
    return RedirectResponse('/vk-hub', status_code=303)


@router.post('/vk-hub/sync')
def vk_hub_sync(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(ChannelAccount).filter(ChannelAccount.channel == 'vk').order_by(ChannelAccount.created_at.desc()).first()
    if not account:
        return RedirectResponse('/vk-hub', status_code=303)
    ok, details = ChannelService(db).sync_vk(account)
    write_log(db, action='VK_COMMUNITY_SYNC' if ok else 'VK_COMMUNITY_SYNC_ERROR', details=details, level='INFO' if ok else 'ERROR', user_id=current_user.id)
    return RedirectResponse('/vk-hub', status_code=303)


@router.post('/vk-hub/reply')
def vk_hub_reply(
    peer_id: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(ChannelAccount).filter(ChannelAccount.channel == 'vk').order_by(ChannelAccount.created_at.desc()).first()
    if not account:
        return RedirectResponse('/vk-hub', status_code=303)
    ok, details = ChannelService(db).send_vk_reply(account, peer_id=peer_id, message=message)
    write_log(db, action='VK_COMMUNITY_REPLY' if ok else 'VK_COMMUNITY_REPLY_ERROR', details=details, level='INFO' if ok else 'ERROR', user_id=current_user.id)
    return RedirectResponse('/vk-hub', status_code=303)


@router.post('/vk-hub/messages/{message_id}/status')
def vk_hub_set_status(
    message_id: int,
    status: str = Form('in_progress'),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = db.query(ChannelMessage).filter(ChannelMessage.id == message_id, ChannelMessage.channel == 'vk').first()
    if msg:
        msg.status = status
        db.commit()
        write_log(db, action='VK_HUB_STATUS', details=f'VK message #{message_id} -> {status}', user_id=current_user.id)
    return RedirectResponse('/vk-hub', status_code=303)
