from db import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UUID, Text, JSON
from datetime import datetime
from uuid import uuid4


class Chart(Base):

    __tablename__ = "charts"

    uuid = Column(
        UUID(as_uuid=True), unique=True, default=uuid4, nullable=False, primary_key=True
    )
    chat_uuid = Column(
        UUID(as_uuid=True), ForeignKey("chat_history.uuid"), nullable=False
    )
    chart_type = Column(String, nullable=False)
    code = Column(Text)
    data = Column(JSON)
    caption = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
