from sqlalchemy.orm import Session
from db.models.chat_history import ChatHistory
from datetime import datetime


class ChatHistoryQuery:

    @staticmethod
    def create_new_chat_history(db: Session, customer_uuid:str, query_type: str, data_source_id: int):
        """
        Creates a new chat history record in the database.

        Args:
            db (Session): The database session.
            customer_uuid (UUID): The UUID of the customer.
            query_type (str): The type of the query.
            data_source_id (int): The ID of the data source.

        Returns:
            ChatHistory: The created chat history object.
        """
        chat_history = ChatHistory(
            customer_uuid=customer_uuid, query_type=query_type, data_source_id=data_source_id
        )
        db.add(chat_history)
        db.flush()

        return chat_history
    
    @staticmethod
    def get_chat_history(db: Session, customer_uuid:str, query_type: str, data_source_id: int):
        """
        Retrieves a chat history record from the database.

        Args:
            db (Session): The database session.
            customer_uuid (UUID): The UUID of the customer.
            query_type (str): The type of the query.
            data_source_id (int): The ID of the data source.

        Returns:
            ChatHistory: The chat history object if found, None otherwise.
        """
        return db.query(ChatHistory).filter(
            ChatHistory.customer_uuid == customer_uuid,
            ChatHistory.query_type == query_type,
            ChatHistory.data_source_id == data_source_id,
        ).first()
    
    @staticmethod
    def is_valid_chat_history(db: Session, chat_uuid: str, query_type: str, customer_uuid: str, data_source_id:int):
        """
        Checks if a chat history record is valid.

        Args:
            db (Session): The database session.
            chat_uuid (str): The UUID of the chat history record.
            query_type (str): The type of the query.
            customer_uuid (str): The UUID of the customer.
            data_source_id (int): The ID of the data source.

        Returns:
            bool: True if the chat history record is valid, False otherwise.
        """
        chat_history = db.query(ChatHistory).filter(
            ChatHistory.uuid == chat_uuid,
            ChatHistory.customer_uuid == customer_uuid,
            ChatHistory.query_type == query_type,
            ChatHistory.data_source_id == data_source_id,
        ).first()

        if chat_history:
            return True
        return False

