from pydantic import BaseModel, EmailStr, model_validator
from typing import List, Optional
from fastapi import HTTPException, status


class CustomerRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str

    @model_validator(mode='after')
    def password_match(cls, v):
        if v.password != v.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password and confirm password do not match"
            )
        return v


class CustomerRegisterResponse(BaseModel):
    message: str
    data: Optional[dict]


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CustomerLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
