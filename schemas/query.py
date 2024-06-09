from pydantic import BaseModel
from typing import Optional
from config import Config

class CustomerQueryRequest(BaseModel):
    query: str
    data_source_id:Optional[int] = None
    model:str = Config.DEFAULT_OPENAI_MODEL


class CustomerQueryResponse(BaseModel):
    query: str
    response: str
    sql_query: Optional[str] = None
    data_source_id:Optional[int] = None
    