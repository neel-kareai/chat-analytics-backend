from sqlalchemy.orm import Session
from db.models.db_config import DBConfig


class DBConfigQuery:
    @staticmethod
    def create_db_config(
        db: Session, customer_uuid: str, db_type: str, db_config: dict
    ) -> DBConfig:
        db_config = DBConfig(
            customer_uuid=customer_uuid, db_type=db_type, db_config=db_config
        )
        db.add(db_config)
        db.flush()
        return db_config

    @staticmethod
    def get_db_config_by_customer_uuid(db: Session, customer_uuid: str):
        return db.query(DBConfig).filter(DBConfig.customer_uuid == customer_uuid).all()
