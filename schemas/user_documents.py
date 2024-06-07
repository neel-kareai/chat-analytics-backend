from pydantic import BaseModel


class UserDocumentUploadResponse(BaseModel):
    document_id: int
    document_name: str
    document_type: str
