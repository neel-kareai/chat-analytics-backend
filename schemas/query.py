from pydantic import BaseModel
from typing import Optional

class CustomerQueryRequest(BaseModel):
    query: str
    db_id: Optional[int] = None
    csv_file_id: Optional[int] = None
    