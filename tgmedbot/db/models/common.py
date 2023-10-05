import datetime

from sqlalchemy import Column, Integer, Boolean, String, DateTime

from .core import *


__all__ = ['UsersTable']


class UsersTable(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    lang = Column(String)
    last_activity_dt = Column(DateTime, default=datetime.datetime.utcnow)
