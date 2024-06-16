from fastapi import (
    APIRouter,
    status,
    Depends,
    Header,
    UploadFile,
    BackgroundTasks,
    Response,
)
from data_response.base_response import APIResponseBase
from helper.auth import get_current_user, AccessTokenData
from logger import logger
from db import get_db
from db.queries.user_documents import UserDocumentQuery
from db.models.user_document import UserDocument
from db.queries.chat_history import ChatHistoryQuery
from schemas.user_documents import UserDocumentUploadResponse
from sqlalchemy.orm import Session
from config import Config
import random
from helper.openai import create_document_embedding


router = APIRouter(prefix="/csv", tags=["csv"])


def process_embedding(db: Session, csv_doc: UserDocument) -> bool:
    """
    Process the embedding for a given CSV document.

    Args:
        db (Session): The database session.
        csv_doc (UserDocument): The CSV document to process.

    Returns:
        bool: True if the embedding was successfully created, False otherwise.
    """
    try:
        logger.debug(f"Creating Embedding for doc id {csv_doc.id}")
        embedding_path = create_document_embedding(
            document_path=csv_doc.document_url, customer_uuid=csv_doc.customer_uuid
        )
        UserDocumentQuery.update_embedding_path(db, csv_doc.id, embedding_path)
        db.commit()
        logger.debug(f"Embedding created for doc id {csv_doc.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to create document embedding: {e}")
        return False


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:
    """
    Uploads a CSV file and processes it.

    Args:
        file (UploadFile): The CSV file to upload.
        background_tasks (BackgroundTasks): Background tasks to be executed.
        response (Response): The HTTP response object.
        current_user (AccessTokenData, optional): The current user's access token data. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        APIResponseBase: The API response containing the status and data.
    """

    logger.debug(f"Request: {file.filename}")

    # Check the file mime type
    if file.content_type != "text/csv":
        logger.error("Invalid file type")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return APIResponseBase.bad_request(message="Invalid file type")

    # Save the file with
    filename = f"./tmp/{random.randbytes(8).hex()}.csv"
    with open(filename, "wb") as f:
        f.write(file.file.read())

    new_csv_doc = UserDocumentQuery.create_user_document(
        db, current_user.uuid, "csv", file.filename, filename, "processing"
    )

    if not new_csv_doc:
        logger.error("Failed to create csv document")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return APIResponseBase.internal_server_error(
            message="Failed to create csv document"
        )

    chat_history = ChatHistoryQuery.create_new_chat_history(
        db, current_user.uuid, "csv", new_csv_doc.id, new_csv_doc.document_name
    )

    db.commit()
    background_tasks.add_task(process_embedding, db, new_csv_doc)

    response.status_code = status.HTTP_201_CREATED
    return APIResponseBase.created(
        message="CSV file uploaded successfully",
        data=UserDocumentUploadResponse(
            document_id=new_csv_doc.id,
            document_name=new_csv_doc.document_name,
            document_type=new_csv_doc.document_type,
        ),
    )
