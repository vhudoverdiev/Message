import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _as_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv('APP_NAME', 'VK CRM Pro')
    secret_key: str = os.getenv('SECRET_KEY', 'change_me')
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./crm.db')
    admin_username: str = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password: str = os.getenv('ADMIN_PASSWORD', 'admin123')
    vk_default_api_version: str = os.getenv('VK_DEFAULT_API_VERSION', '5.199')
    vk_default_poll_wait: int = _as_int('VK_DEFAULT_POLL_WAIT', 25)
    static_asset_version: str = os.getenv('STATIC_ASSET_VERSION', '1')


settings = Settings()
