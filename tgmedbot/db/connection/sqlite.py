import asyncio

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncConnection, AsyncEngine
from ...constants.db import BotDataBaseConstants


__all__ = ['SqliteConnection', 'SqliteConnectionModel']


class SqliteConnectionModel:
    def __init__(self):
        self.engine_uri = f'{BotDataBaseConstants.DB_DRIVER}:///{BotDataBaseConstants.DATABASE_PATH}'
        # echo for logging all sql-statements to the console adn future for 2.0 features support
        self.async_engine: AsyncEngine = create_async_engine(self.engine_uri, echo=True, future=True)
        # Create a sessionmaker
        self.async_sessionmaker = sessionmaker(self.async_engine, class_=AsyncSession, expire_on_commit=True)

        self.lock = asyncio.Lock()

    @property
    def engine_uri(self) -> str:
        return self._engine_uri

    @engine_uri.setter
    def engine_uri(self, value: str):
        if not isinstance(value, str):
            raise AssertionError(f"`engine_uri` must be of type string but got {type(value)}")
        self._engine_uri = value

    def get_session(self) -> AsyncSession:
        return self.async_sessionmaker()


SqliteConnection = SqliteConnectionModel()
