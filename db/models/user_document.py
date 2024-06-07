from db import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, UUID, ForeignKey
from uuid import uuid4
from datetime import datetime


class UserDocument(Base):
    __tablename__ = 'user_documents'

    id = Column(Integer, primary_key=True, index=True)
    customer_uuid = Column(UUID(as_uuid=True), ForeignKey(
        'customers.uuid'), nullable=False)
    document_type = Column(String, nullable=False)
    document_name = Column(String, nullable=False)
    document_url = Column(String, nullable=False)
    embed_url = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)
