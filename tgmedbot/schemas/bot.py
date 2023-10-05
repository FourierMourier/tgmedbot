import pydantic


__all__ = ['BotConfigModel']


class BotConfigModel(pydantic.BaseModel):
    token: pydantic.StrictStr


