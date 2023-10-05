from ..constants.common import PROJECT_ROOT

__all__ = ['BotDataBaseConstants']


class BotDataBaseConstants:
    TABLE_NAME: str = 'users'
    DB_NAME: str = 'tgmedbot.sqlite3'

    DB_DRIVER: str = r'sqlite+aiosqlite'
    DATABASE_PATH: str = str(PROJECT_ROOT / 'bot' / DB_NAME)
