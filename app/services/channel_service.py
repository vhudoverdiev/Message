from __future__ import annotations

from base64 import urlsafe_b64decode
from datetime import datetime
from email.utils import parseaddr
from json import loads
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.core.security import TokenCipher
from app.models.channel_account import ChannelAccount
from app.models.channel_message import ChannelMessage


class ChannelService:
    def __init__(self, db: Session):
        self.db = db

    def list_accounts(self, channel: str) -> list[ChannelAccount]:
        return self.db.query(ChannelAccount).filter(ChannelAccount.channel == channel).order_by(ChannelAccount.created_at.desc()).all()

    def upsert_account(self, channel: str, account_id: int | None, name: str, external_id: str, token: str) -> ChannelAccount:
        account = self.db.query(ChannelAccount).filter(ChannelAccount.id == account_id).first() if account_id else None
        if not account:
            account = ChannelAccount(channel=channel, name=name, external_id=external_id)
            self.db.add(account)
        account.name = name
        account.external_id = external_id
        if token:
            account.token_encrypted = TokenCipher.encrypt(token)
        account.status = 'active' if account.token_encrypted else 'inactive'
        self.db.commit()
        return account

    def sync_gmail(self, account: ChannelAccount, search_query: str = '') -> tuple[bool, str]:
        token = TokenCipher.decrypt(account.token_encrypted)
        if not token:
            return False, 'Требуется OAuth access token Gmail.'

        params = {'maxResults': 20}
        if search_query:
            params['q'] = search_query
        endpoint = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?{urlencode(params)}"
        ok, data = self._request_json(endpoint, token)
        if not ok:
            return False, data

        inserted = 0
        for item in data.get('messages', []):
            msg_id = item.get('id')
            if not msg_id:
                continue
            detail_ok, payload = self._request_json(
                f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full',
                token,
            )
            if not detail_ok:
                continue

            headers = {h.get('name', '').lower(): h.get('value', '') for h in payload.get('payload', {}).get('headers', [])}
            sender = parseaddr(headers.get('from', ''))[0] or headers.get('from', '')
            subject = headers.get('subject', '(без темы)')
            snippet = payload.get('snippet', '')
            body = self._extract_gmail_body(payload)
            internal_date = payload.get('internalDate')
            created = datetime.utcfromtimestamp(int(internal_date) / 1000) if internal_date else datetime.utcnow()
            labels = payload.get('labelIds', [])
            is_read = 'UNREAD' not in labels

            exists = self.db.query(ChannelMessage).filter(
                ChannelMessage.channel == 'gmail',
                ChannelMessage.account_id == account.id,
                ChannelMessage.external_message_id == msg_id,
            ).first()
            if exists:
                exists.subject = subject
                exists.sender_name = sender
                exists.body_preview = snippet
                exists.body_full = body
                exists.is_read = is_read
                exists.status = 'processed' if is_read else 'new'
                continue

            self.db.add(ChannelMessage(
                channel='gmail',
                account_id=account.id,
                external_message_id=msg_id,
                conversation_id=payload.get('threadId', ''),
                sender_name=sender,
                subject=subject,
                body_preview=snippet,
                body_full=body,
                is_read=is_read,
                status='processed' if is_read else 'new',
                created_at=created,
            ))
            inserted += 1
        self.db.commit()
        return True, f'Gmail синхронизирован. Новых писем: {inserted}'

    def sync_telegram(self, account: ChannelAccount) -> tuple[bool, str]:
        token = TokenCipher.decrypt(account.token_encrypted)
        if not token:
            return False, 'Требуется Telegram Bot Token.'

        endpoint = f'https://api.telegram.org/bot{token}/getUpdates?timeout=1&limit=50'
        ok, data = self._request_json(endpoint)
        if not ok:
            return False, data

        inserted = 0
        for upd in data.get('result', []):
            message = upd.get('message') or upd.get('channel_post') or {}
            if not message:
                continue
            message_id = str(message.get('message_id', ''))
            chat = message.get('from') or message.get('chat') or {}
            sender = (chat.get('first_name', '') + ' ' + chat.get('last_name', '')).strip() or chat.get('username', 'Unknown')
            text = message.get('text') or message.get('caption') or '[медиа/системное сообщение]'
            created = datetime.utcfromtimestamp(message.get('date', 0)) if message.get('date') else datetime.utcnow()
            conv_id = str((message.get('chat') or {}).get('id', ''))

            exists = self.db.query(ChannelMessage).filter(
                ChannelMessage.channel == 'telegram',
                ChannelMessage.account_id == account.id,
                ChannelMessage.external_message_id == message_id,
                ChannelMessage.conversation_id == conv_id,
            ).first()
            if exists:
                continue

            self.db.add(ChannelMessage(
                channel='telegram',
                account_id=account.id,
                external_message_id=message_id,
                conversation_id=conv_id,
                sender_name=sender,
                subject='Telegram notification',
                body_preview=text,
                body_full=text,
                status='new',
                is_read=False,
                created_at=created,
            ))
            inserted += 1

        self.db.commit()
        return True, f'Telegram синхронизирован. Новых уведомлений: {inserted}'

    def sync_vk(self, account: ChannelAccount) -> tuple[bool, str]:
        token = TokenCipher.decrypt(account.token_encrypted)
        if not token:
            return False, 'Требуется VK API token сообщества.'

        params = urlencode({'access_token': token, 'v': '5.199', 'count': 20})
        endpoint = f'https://api.vk.com/method/messages.getConversations?{params}'
        ok, data = self._request_json(endpoint)
        if not ok:
            return False, data
        if data.get('error'):
            return False, data['error'].get('error_msg', 'VK API error')

        response = data.get('response', {})
        inserted = 0
        for item in response.get('items', []):
            last = item.get('last_message', {})
            text = (last.get('text') or '').strip() or '[вложение/служебное сообщение]'
            peer_id = str((item.get('conversation') or {}).get('peer', {}).get('id', ''))
            msg_id = str(last.get('id', ''))
            created = datetime.utcfromtimestamp(last.get('date', 0)) if last.get('date') else datetime.utcnow()
            sender = str(last.get('from_id', 'VK User'))

            exists = self.db.query(ChannelMessage).filter(
                ChannelMessage.channel == 'vk',
                ChannelMessage.account_id == account.id,
                ChannelMessage.external_message_id == msg_id,
            ).first()
            if exists:
                continue

            self.db.add(ChannelMessage(
                channel='vk',
                account_id=account.id,
                external_message_id=msg_id,
                conversation_id=peer_id,
                sender_name=sender,
                subject='VK dialogue',
                body_preview=text,
                body_full=text,
                status='new',
                is_read=False,
                created_at=created,
            ))
            inserted += 1

        self.db.commit()
        return True, f'VK сообщения синхронизированы. Новых: {inserted}'

    def send_vk_reply(self, account: ChannelAccount, peer_id: str, message: str) -> tuple[bool, str]:
        token = TokenCipher.decrypt(account.token_encrypted)
        if not token:
            return False, 'Требуется VK API token.'

        params = urlencode({
            'access_token': token,
            'v': '5.199',
            'peer_id': peer_id,
            'random_id': int(datetime.utcnow().timestamp()),
            'message': message,
        })
        endpoint = f'https://api.vk.com/method/messages.send?{params}'
        ok, data = self._request_json(endpoint)
        if not ok:
            return False, data
        if data.get('error'):
            return False, data['error'].get('error_msg', 'VK API error')
        return True, 'Ответ отправлен в VK.'

    @staticmethod
    def _extract_gmail_body(payload: dict) -> str:
        parts = payload.get('payload', {}).get('parts') or []
        body_data = payload.get('payload', {}).get('body', {}).get('data', '')
        if not body_data:
            for part in parts:
                if part.get('mimeType', '').startswith('text/plain'):
                    body_data = part.get('body', {}).get('data', '')
                    if body_data:
                        break
        if not body_data:
            return payload.get('snippet', '')
        padded = body_data + '=' * (-len(body_data) % 4)
        try:
            return urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8', errors='ignore')
        except ValueError:
            return payload.get('snippet', '')

    @staticmethod
    def _request_json(endpoint: str, bearer_token: str | None = None) -> tuple[bool, dict | str]:
        req = Request(endpoint)
        if bearer_token:
            req.add_header('Authorization', f'Bearer {bearer_token}')
        try:
            with urlopen(req, timeout=20) as response:
                return True, loads(response.read().decode('utf-8'))
        except URLError:
            return False, 'Ошибка сети/API при обращении к каналу.'
