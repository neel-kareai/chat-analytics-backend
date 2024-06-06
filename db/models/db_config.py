from db import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UUID, JSON
from datetime import datetime
from uuid import uuid4
from json import JSONEncoder


class DBConfig(Base):
    __tablename__ = 'db_configs'

    id = Column(Integer, primary_key=True, index=True)
    customer_uuid = Column(UUID(as_uuid=True), ForeignKey(
        'customers.uuid'), nullable=False)
    db_type = Column(String, nullable=False)
    db_config = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "customer_uuid": self.customer_uuid,
            "db_type": self.db_type,
            "db_config": self.db_config,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }