from sqlalchemy.orm import Session
from db.models.user_document import UserDocument
from typing import List


class UserDocumentQuery:
    @staticmethod
    def create_user_document(
        db: Session,
        customer_uuid: str,
        document_type: str,
        document_name: str,
        document_url: str,
        embed_url: str,
    ) -> UserDocument:
        """
        Create a new user document and save it to the database.

        Args:
            db (Session): The database session.
            customer_uuid (str): The UUID of the customer.
            document_type (str): The type of the document.
            document_name (str): The name of the document.
            document_url (str): The URL of the document.
            embed_url (str): The URL for embedding the document.

        Returns:
            UserDocument: The created user document.
        """
        user_document = UserDocument(
            customer_uuid=customer_uuid,
            document_type=document_type,
            document_name=document_name,
            document_url=document_url,
            embed_url=embed_url,
        )
        db.add(user_document)
        db.flush()
        return user_document

    @staticmethod
    def get_user_document_by_id(db: Session, user_document_id: int) -> UserDocument:
        """
        Retrieve a user document by its ID.

        Args:
            db (Session): The database session.
            user_document_id (int): The ID of the user document.

        Returns:
            UserDocument: The retrieved user document.
        """
        return db.query(UserDocument).filter(UserDocument.id == user_document_id).first()

    @staticmethod
    def get_user_documents_by_customer_uuid(db: Session, customer_uuid: str) -> List[UserDocument]:
        """
        Retrieve all user documents for a given customer UUID.

        Args:
            db (Session): The database session.
            customer_uuid (str): The UUID of the customer.

        Returns:
            List[UserDocument]: A list of user documents.
        """
        return db.query(UserDocument).filter(UserDocument.customer_uuid == customer_uuid).all()

    @staticmethod
    def update_embedding_path(db:Session, user_document_id:int, embedding_path:str):
        """
        Update the embedding path of a user document.

        Args:
            db (Session): The database session.
            user_document_id (int): The ID of the user document.
            embedding_path (str): The new embedding path.

        Returns:
            UserDocument: The updated user document.
        """
        user_document = db.query(UserDocument).filter(UserDocument.id == user_document_id).first()
        user_document.embed_url = embedding_path
        user_document.is_embedded = True
        db.flush()
        return user_document

    @staticmethod
    def delete_user_document(db: Session, user_document_id: int) -> bool:
        """
        Delete a user document from the database.

        Args:
            db (Session): The database session.
            user_document_id (int): The ID of the user document.

        Returns:
            bool: True if the user document was successfully deleted, False otherwise.
        """
        raise NotImplementedError("Method not implemented")
