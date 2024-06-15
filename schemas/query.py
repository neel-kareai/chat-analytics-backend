from pydantic import BaseModel
from typing import Optional
from config import Config


class CustomerQueryRequest(BaseModel):
    """
    Represents a customer query request.

    Attributes:
        query (str): The query string.
        data_source_id (Optional[int]): The ID of the data source (default: None).
        model (str): The OpenAI model to use (default: Config.DEFAULT_OPENAI_MODEL).
    """

    query: str
    data_source_id: Optional[int] = None
    model: str = Config.DEFAULT_OPENAI_MODEL
    chat_uuid: Optional[str] = None


class CustomerQueryResponse(BaseModel):
    """
    Represents a customer query response.

    Attributes:
        query (str): The query string.
        response (str): The response string.
        sql_query (Optional[str]): The SQL query (default: None).
        data_source_id (Optional[int]): The ID of the data source (default: None).
    """

    query: str
    response: str
    sql_query: Optional[str] = None
    data_source_id: Optional[int] = None
    chat_uuid: str
