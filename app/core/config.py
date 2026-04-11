from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'VK CRM Pro'
    secret_key: str = 'change_me'
    database_url: str = 'sqlite:///./crm.db'
    admin_username: str = 'admin'
    admin_password: str = 'admin123'
    vk_default_api_version: str = '5.199'
    vk_default_poll_wait: int = 25


settings = Settings()
