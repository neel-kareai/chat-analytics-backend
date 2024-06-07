from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()


class Config:

    # PROJECT
    PROJECT_NAME = 'Analytics Agent'
    PROJECT_VERSION = '1.0'

    # DB
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES'))
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES = int(
        os.getenv('JWT_REFRESH_TOKEN_EXPIRE_MINUTES'))

    # OPENAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    DEFAULT_OPENAI_MODEL = os.getenv('DEFAULT_OPENAI_MODEL')
    DEFAULT_OPENAI_EMBEDDING_MODEL = os.getenv(
        'DEFAULT_OPENAI_EMBEDDING_MODEL')

    # CHROMA
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH')
