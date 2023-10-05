import datetime
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UsersTable
from ...schemas.common import UserModel
from ...utils.common import infoColorstr
from typing import Optional

__all__ = ['delete_inactive_users', 'get_user_by_id']


async def delete_inactive_users(session: AsyncSession, cutoff_time: datetime.datetime) -> int:
    # Query all inactive users to delete
    stmt = sqlalchemy.select(UsersTable).filter(sqlalchemy.or_(
        UsersTable.last_activity_dt == None,
        UsersTable.last_activity_dt < cutoff_time
    ))
    # TODO: consider to delete max users per 1 statement with
    #               stmt = stmt.limit(max_deletions_per_statement)
    results = await session.execute(stmt)
    users_to_delete = results.scalars().all()
    if len(users_to_delete) == 0:
        return len(users_to_delete)
    # Delete inactive users from the database here
    for user in users_to_delete:
        stmt = sqlalchemy.delete(UsersTable).where(UsersTable.id == user.id)
        await session.execute(stmt)
        # OR simply: # may not work with `AsyncSession` object because .query is not there
        # session.delete(user)

    await session.commit()
    return len(users_to_delete)


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[UserModel]:
    statement = sqlalchemy.select(UsersTable).filter(UsersTable.id == user_id)
    results = await session.execute(statement)
    user_result = results.first()
    if user_result:
        # [c.name for c in user_result[0].__table__.c]
        return UserModel(**{c.name: getattr(user_result[0], c.name) for c in user_result[0].__table__.c})
    else:
        return None


async def add_new_user(session: AsyncSession, user_id: int, curr_dt: datetime.datetime) -> None:
    new_user = UsersTable(
        id=user_id,
        # created_at=curr_dt,
        last_activity_dt=curr_dt,
    )

    # async with session.begin():
    session.add(new_user)
    await session.commit()
    print(infoColorstr(f"created user id={user_id} at {curr_dt}"))
