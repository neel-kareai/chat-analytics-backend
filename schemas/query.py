from pydantic import BaseModel
from typing import Optional

class CustomerQueryRequest(BaseModel):
    query: str
    db_id: Optional[int] = None
    csv_file_id: Optional[int] = None


class CustomerQueryResponse(BaseModel):
    query: str
    response: str
    sql_query: Optional[str] = None
    db_id: Optional[int] = None
    csv_file_id: Optional[int] = None
    