from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import base, user
from app.models.client import Client
from app.models.setting import Setting
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
    ensure_schema_updates()
    seed_admin_user()
    seed_demo_data()


def ensure_schema_updates() -> None:
    """Мягкие schema-обновления для уже существующей SQLite/PostgreSQL базы."""
    with engine.begin() as connection:
        if engine.dialect.name == 'sqlite':
            columns = {
                row[1]
                for row in connection.execute(text('PRAGMA table_info(vk_accounts)')).fetchall()
            }
            if 'avatar_url' not in columns:
                connection.execute(text("ALTER TABLE vk_accounts ADD COLUMN avatar_url VARCHAR(500) DEFAULT ''"))
        else:
            exists = connection.execute(text("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='vk_accounts' AND column_name='avatar_url'
                LIMIT 1
            """)).first()
            if not exists:
                connection.execute(text("ALTER TABLE vk_accounts ADD COLUMN avatar_url VARCHAR(500) DEFAULT ''"))


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
        if not db.query(Client).first():
            db.add(Client(
                full_name='Иван Петров',
                vk_link='https://vk.com/id1',
                vk_user_id='1',
                tags='new,vip',
                status='new',
                notes='Нужна консультация',
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
