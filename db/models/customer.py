from db import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, UUID, LargeBinary
from datetime import datetime
from uuid import uuid4


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True,
                  default=uuid4, nullable=False)
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
