from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.vk_account import VKAccount


class VKService:
    """Точка расширения для реального VK API/Long Poll/Callback integration."""

    def __init__(self, db: Session):
        self.db = db

    def validate_connection(self, account: VKAccount) -> tuple[bool, str]:
        # Здесь нужно вызвать VK API метод groups.getById/messages.getLongPollServer.
        if not account.access_token:
            return False, 'Token отсутствует'
        return True, 'Подключение настроено'

    def sync_messages_stub(self, account: VKAccount) -> int:
        """Заглушка для тестовых данных; заменить реальным long poll fetch."""
        sample = Message(
            vk_account_id=account.id,
            dialog_id=f'dialog_{account.group_id}',
            direction='in',
            text='Тестовое сообщение из VK adapter. Замените на реальный API вызов.',
            is_read=False,
        )
        self.db.add(sample)
        self.db.commit()
        return 1

    def long_poll_config_map(self, account: VKAccount) -> dict[str, str]:
        return {
            'group_id': account.group_id,
            'access_token': account.access_token,
            'long_poll_server': account.long_poll_server,
            'long_poll_key': account.long_poll_key,
            'long_poll_ts': account.long_poll_ts,
        }
