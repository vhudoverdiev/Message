from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.channel_account import ChannelAccount
from app.models.channel_message import ChannelMessage


def get_dashboard_stats(db: Session) -> dict[str, int]:
    accounts = db.query(func.count(ChannelAccount.id)).filter(ChannelAccount.channel == 'vk').scalar() or 0
    new_messages = db.query(func.count(ChannelMessage.id)).filter(
        ChannelMessage.channel == 'vk',
        ChannelMessage.is_read.is_(False),
    ).scalar() or 0
    clients = db.query(func.count(Client.id)).scalar() or 0
    active_dialogs = db.query(func.count(func.distinct(ChannelMessage.conversation_id))).filter(ChannelMessage.channel == 'vk').scalar() or 0
    return {
        'accounts': accounts,
        'new_messages': new_messages,
        'clients': clients,
        'dialogs': active_dialogs,
    }
