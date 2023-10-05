"""
    The sole purpose of this script is just to be imported somewhere else to make sure database is created
"""

import os
from pathlib import Path
import sqlite3
import pydantic
from typing import Optional, List, Dict
import datetime

import asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncConnection

from ..constants.db import BotDataBaseConstants
from ..utils.common import infoColorstr
from .connection.sqlite import SqliteConnection
from .models import Base, UsersTable

# prevent any imports from here since you're not supposed to accidentally use anything from here
__all__ = []

# check for the base folder existence:
Path(BotDataBaseConstants.DATABASE_PATH).absolute().parent.mkdir(exist_ok=True)


async def check_table_existence(table_name: str, conn: AsyncConnection) -> bool:
    # not able to do the following:
    # inspector = sqlalchemy.inspect(conn)
    # return await conn.run_sync(
    #     inspector.has_table, table_name, schema=None
    # )
    # see
    #   https://docs.sqlalchemy.org/en/20/errors.html#error-xd3s
    # inspector = sqlalchemy.inspect(conn)
    tables = await conn.run_sync(
        lambda sync_conn: sqlalchemy.inspect(sync_conn).get_table_names()
    )
    return table_name in tables


# create the users table if it doesn't exist
async def create_users_table():
    async with SqliteConnection.async_engine.begin() as conn:
        # async with async_sessionmaker() as session:
        if not await check_table_existence(UsersTable.__tablename__, conn):  # session):
            await conn.run_sync(Base.metadata.create_all)
        else:
            print(infoColorstr(f"There's already database with users table at {SqliteConnection.engine_uri}"))

# create the users table when the module is imported
asyncio.run(create_users_table())
