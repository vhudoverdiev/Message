from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.message import Message
from app.models.vk_account import VKAccount


def get_dashboard_stats(db: Session) -> dict[str, int]:
    accounts = db.query(func.count(VKAccount.id)).scalar() or 0
    new_messages = db.query(func.count(Message.id)).filter(Message.is_read.is_(False)).scalar() or 0
    clients = db.query(func.count(Client.id)).scalar() or 0
    active_dialogs = db.query(func.count(func.distinct(Message.dialog_id))).scalar() or 0
    return {
        'accounts': accounts,
        'new_messages': new_messages,
        'clients': clients,
        'dialogs': active_dialogs,
    }
