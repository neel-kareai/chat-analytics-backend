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
        return db.query(UserDocument).filter(UserDocument.id == user_document_id).first()

    @staticmethod
    def get_user_documents_by_customer_uuid(db: Session, customer_uuid: str) -> List[UserDocument]:
        return db.query(UserDocument).filter(UserDocument.customer_uuid == customer_uuid).all()

    @staticmethod
    def update_embedding_path(db:Session, user_document_id:int, embedding_path:str):
        user_document = db.query(UserDocument).filter(UserDocument.id == user_document_id).first()
        user_document.embed_url = embedding_path
        user_document.is_embedded = True
        db.flush()
        return user_document
        

    @staticmethod
    def delete_user_document(db: Session, user_document_id: int) -> bool:
        raise NotImplementedError("Method not implemented")
