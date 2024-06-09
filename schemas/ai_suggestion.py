from pydantic import BaseModel
from typing import Optional, List


class AISuggestionRequest(BaseModel):
    last_ques: Optional[str] = None
    data_source_id: Optional[int] = None
    query_type: Optional[str] = None
    is_first_request: bool = False


class AISuggestionResponse(BaseModel):
    suggestions: List[str]
