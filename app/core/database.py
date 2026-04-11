from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import base, user
from app.models.client import Client
from app.models.message import Message
from app.models.setting import Setting
from app.models.vk_account import VKAccount
from app.services.auth_service import hash_password

is_sqlite = settings.database_url.startswith('sqlite')
engine = create_engine(settings.database_url, connect_args={'check_same_thread': False} if is_sqlite else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    base.Base.metadata.create_all(bind=engine)
    seed_admin_user()
    seed_demo_data()


def seed_admin_user() -> None:
    db = SessionLocal()
    try:
        existing = db.query(user.User).filter(user.User.username == settings.admin_username).first()
        if existing:
            return
        admin = user.User(
            username=settings.admin_username,
            full_name='System Administrator',
            role='admin',
            password_hash=hash_password(settings.admin_password),
            is_active=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        if not db.query(VKAccount).first():
            account = VKAccount(
                name='Main Store',
                group_id='club123456',
                status='active',
                access_token='demo_token_here',
                long_poll_server='https://lp.vk.com/demo',
                long_poll_key='demo_key',
                long_poll_ts='1',
                description='Демо аккаунт для старта',
            )
            db.add(account)
            db.flush()

            client = Client(
                full_name='Иван Петров',
                vk_link='https://vk.com/id1',
                vk_user_id='1',
                tags='new,vip',
                status='new',
                notes='Нужна консультация',
            )
            db.add(client)
            db.flush()

            db.add(Message(
                vk_account_id=account.id,
                client_id=client.id,
                dialog_id='dialog_1',
                direction='in',
                text='Здравствуйте, интересует цена.',
                is_read=False,
            ))

        if not db.query(Setting).first():
            db.add_all([
                Setting(group_name='system', key='crm_name', value='VK CRM Pro'),
                Setting(group_name='notifications', key='email_enabled', value='false'),
                Setting(group_name='crm', key='default_timezone', value='UTC'),
            ])

        db.commit()
    finally:
        db.close()
