from datetime import datetime
from json import loads
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.vk_account import VKAccount


class VKService:
    """Точка расширения для реального VK API/Long Poll/Callback integration."""

    API_URL = 'https://api.vk.com/method'
    API_VERSION = '5.199'

    def __init__(self, db: Session):
        self.db = db

    def validate_connection(self, account: VKAccount) -> tuple[bool, str]:
        if not account.access_token:
            return False, 'Токен отсутствует'

        ok, payload = self._vk_api_request('users.get', account.access_token, {'fields': 'photo_100'})
        if not ok:
            return False, payload

        user = payload[0]
        account.avatar_url = user.get('photo_100', '') or ''
        full_name = f"{user.get('first_name', '').strip()} {user.get('last_name', '').strip()}".strip()
        return True, f'Токен подтвержден: {full_name or "VK user"}'

    def sync_dialogs(self, account: VKAccount, limit: int = 30) -> tuple[bool, int, str]:
        if not account.access_token:
            return False, 0, 'Токен отсутствует'

        ok, response = self._vk_api_request(
            'messages.getConversations',
            account.access_token,
            {'count': max(1, min(limit, 200)), 'filter': 'all'},
        )
        if not ok:
            return False, 0, response

        items = response.get('items', [])
        synced = 0
        for item in items:
            conversation = item.get('conversation', {})
            peer = conversation.get('peer', {})
            peer_id = peer.get('id')
            if not peer_id:
                continue

            last_message = item.get('last_message') or {}
            text = (last_message.get('text') or '').strip()
            if not text:
                text = '[вложение/служебное сообщение]'

            sent_unix = last_message.get('date')
            sent_at = datetime.utcfromtimestamp(sent_unix) if sent_unix else datetime.utcnow()
            outgoing = bool(last_message.get('out'))

            duplicate = (
                self.db.query(Message)
                .filter(
                    Message.vk_account_id == account.id,
                    Message.dialog_id == str(peer_id),
                    Message.text == text,
                    Message.sent_at == sent_at,
                )
                .first()
            )
            if duplicate:
                continue

            self.db.add(Message(
                vk_account_id=account.id,
                dialog_id=str(peer_id),
                direction='out' if outgoing else 'in',
                text=text,
                is_read=not conversation.get('unanswered', False),
                sent_at=sent_at,
            ))
            synced += 1

        self.db.commit()
        return True, synced, f'Синхронизировано диалогов: {len(items)}, новых сообщений: {synced}'

    def long_poll_config_map(self, account: VKAccount) -> dict[str, str]:
        return {
            'group_id': account.group_id,
            'access_token': account.access_token,
            'long_poll_server': account.long_poll_server,
            'long_poll_key': account.long_poll_key,
            'long_poll_ts': account.long_poll_ts,
        }

    def _vk_api_request(self, method: str, token: str, params: dict | None = None) -> tuple[bool, dict | list | str]:
        payload = {
            'access_token': token,
            'v': self.API_VERSION,
        }
        if params:
            payload.update(params)

        url = f"{self.API_URL}/{method}?{urlencode(payload)}"
        try:
            with urlopen(url, timeout=15) as response:
                data = loads(response.read().decode('utf-8'))
        except URLError:
            return False, 'Не удалось связаться с VK API. Проверьте сеть и токен.'

        if data.get('error'):
            err = data['error']
            code = err.get('error_code', '-')
            message = err.get('error_msg', 'Неизвестная ошибка VK API')
            return False, f'VK API error {code}: {message}'

        return True, data.get('response', {})
