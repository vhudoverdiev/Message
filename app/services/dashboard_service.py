from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.channel_account import ChannelAccount
from app.models.channel_message import ChannelMessage


def _count_unread_by_channel(db: Session, channel: str) -> int:
    return db.query(func.count(ChannelMessage.id)).filter(
        ChannelMessage.channel == channel,
        ChannelMessage.is_read.is_(False),
    ).scalar() or 0


def get_dashboard_stats(db: Session) -> dict[str, int | dict[str, dict[str, int | str | bool]]]:
    accounts = db.query(func.count(ChannelAccount.id)).filter(ChannelAccount.channel == 'vk').scalar() or 0
    clients = db.query(func.count(Client.id)).scalar() or 0
    active_dialogs = db.query(func.count(func.distinct(ChannelMessage.conversation_id))).filter(ChannelMessage.channel == 'vk').scalar() or 0

    vk_new = _count_unread_by_channel(db, 'vk')
    telegram_new = _count_unread_by_channel(db, 'telegram')
    gmail_new = _count_unread_by_channel(db, 'gmail')

    return {
        'accounts': accounts,
        'new_messages': vk_new,
        'clients': clients,
        'dialogs': active_dialogs,
        'notifications': {
            'vk': {
                'title': 'Новые сообщения VK',
                'count': vk_new,
                'empty_text': 'Нет новых сообщений',
                'link': '/messages',
            },
            'telegram': {
                'title': 'Новые уведомления Telegram',
                'count': telegram_new,
                'empty_text': 'Нет новых уведомлений',
                'link': '/telegram',
            },
            'gmail': {
                'title': 'Новые сообщения Gmail',
                'count': gmail_new,
                'empty_text': 'Нет новых сообщений',
                'link': '/gmail',
            },
        },
    }
