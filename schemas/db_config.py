from pydantic import BaseModel, field_validator
from typing import List, Optional


class NewDBCreateRequest(BaseModel):
    db_type: str
    db_config: dict

    @field_validator('db_type')
    def check_db_type(cls, value):
        if value not in ['mysql', 'postgres', 'sqlite']:
            raise ValueError('Invalid db_type')
        return value


class NewDBCreateResponse(BaseModel):
    db_config_id: int
    message: str
