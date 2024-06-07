from fastapi import APIRouter, status, Depends, Header, UploadFile
from data_response.base_response import APIResponseBase
from helper.auth import get_current_user, AccessTokenData
from logger import logger
from db import get_db
from db.queries.user_documents import UserDocumentQuery
from schemas.user_documents import UserDocumentUploadResponse
from sqlalchemy.orm import Session
from config import Config
import random
from helper.openai import create_document_embedding


router = APIRouter(prefix="/csv", tags=["csv"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_csv(file: UploadFile,
                     current_user: AccessTokenData = Depends(get_current_user),
                     db: Session = Depends(get_db)
                     ) -> APIResponseBase:
    """
        Upload a CSV file
    """

    logger.debug(f"Request: {file.filename}")

    # Check the file mime type
    if file.content_type != "text/csv":
        logger.error("Invalid file type")
        return APIResponseBase.bad_request(
            message="Invalid file type"
        )

    # Save the file with
    filename = f"./tmp/{random.randbytes(8).hex()}.csv"
    with open(filename, "wb") as f:
        f.write(file.file.read())

    embedding_path = create_document_embedding(
        document_path=filename,
        customer_uuid=current_user.uuid
    )

    new_csv_doc = UserDocumentQuery.create_user_document(
        db, current_user.uuid, "csv", file.filename, filename, embedding_path
    )

    if not new_csv_doc:
        logger.error("Failed to create csv document")
        return APIResponseBase.internal_server_error(
            message="Failed to create csv document"
        )

    db.commit()

    return APIResponseBase.created(
        message="CSV file uploaded successfully",
        data=UserDocumentUploadResponse(
            document_id=new_csv_doc.id,
            document_name=new_csv_doc.document_name,
            document_type=new_csv_doc.document_type,
        )
    )
