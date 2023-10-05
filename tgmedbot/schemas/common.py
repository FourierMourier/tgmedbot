import datetime

import pydantic

from typing import Optional


__all__ = ['UserModel']


class UserModel(pydantic.BaseModel):
    id: int
    lang: Optional[str]
    last_activity_dt: Optional[datetime.datetime]
