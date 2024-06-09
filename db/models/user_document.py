from db import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, UUID, ForeignKey, Boolean
from datetime import datetime


class UserDocument(Base):
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, index=True)
    customer_uuid = Column(
        UUID(as_uuid=True), ForeignKey("customers.uuid"), nullable=False
    )
    document_type = Column(String, nullable=False)
    document_name = Column(String, nullable=False)
    document_url = Column(String, nullable=False)
    is_embedded = Column(Boolean, default=False)
    embed_url = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "document_type": self.document_type,
            "document_name": self.document_name,
            "document_url": self.document_url,
            "is_embedded": self.is_embedded,
            "embed_url": self.embed_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
