import jwt
import datetime
from typing import Optional
from pydantic import BaseModel
from config import Config
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status, Depends

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="customer/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = JWTHandler.decode_access_token(token)
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


class AccessTokenData(BaseModel):
    uuid: str
    email: str
    name: str


class RefreshTokenData(BaseModel):
    uuid: str


class JWTHandler:
    SECRET_KEY = Config.JWT_SECRET_KEY
    ALGORITHM = Config.JWT_ALGORITHM

    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, JWTHandler.SECRET_KEY, algorithm=JWTHandler.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict):
        to_encode = data.copy()
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            days=Config.JWT_REFRESH_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, JWTHandler.SECRET_KEY, algorithm=JWTHandler.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str):
        try:
            payload = jwt.decode(
                token, JWTHandler.SECRET_KEY, algorithms=[JWTHandler.ALGORITHM]
            )
            return AccessTokenData(**payload)
        except jwt.PyJWTError as e:
            raise e

    @staticmethod
    def decode_refresh_token(token: str):
        try:
            payload = jwt.decode(
                token, JWTHandler.SECRET_KEY, algorithms=[JWTHandler.ALGORITHM]
            )
            print(payload)
            return RefreshTokenData(**payload)
        except jwt.PyJWTError:
            return None
