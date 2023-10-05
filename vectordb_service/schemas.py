import pydantic

from typing import Optional


class QueryModel(pydantic.BaseModel):
    user_query: str
    collection_name: Optional[str] = None
    n_results: Optional[int] = 2
