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
from schemas.user_documents import UserDocumentUploadResponse, UserDocumentUpdateRequest
from sqlalchemy.orm import Session
from config import Config
import random
import os
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


@router.get("/{document_id}")
async def get_csv_document(
    document_id: int,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:
    """
    Retrieves the CSV document with the given ID.

    Args:
        document_id (int): The ID of the CSV document to retrieve.
        response (Response): The HTTP response object.
        current_user (AccessTokenData, optional): The current user's access token data. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        APIResponseBase: The API response containing the status and data.
    """

    csv_doc = UserDocumentQuery.get_user_document_by_id(db, document_id, "csv")

    if not csv_doc:
        logger.error("CSV document not found")
        response.status_code = status.HTTP_404_NOT_FOUND
        return APIResponseBase.not_found(message="CSV document not found")

    if str(csv_doc.customer_uuid) != current_user.uuid:
        logger.error("Unauthorized access")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return APIResponseBase.unauthorized(message="Unauthorized access")

    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="CSV document retrieved successfully",
        data=UserDocumentUploadResponse(
            document_id=csv_doc.id,
            document_name=csv_doc.document_name,
            document_type=csv_doc.document_type,
        ),
    )


@router.put("/{document_id}")
def update_csv_document_name(
    document_id: int,
    request: UserDocumentUpdateRequest,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:
    """
    Updates the name of the CSV document with the given ID.

    Args:
        document_id (int): The ID of the CSV document to update.
        request (UserDocumentUpdateRequest): The request object containing the new name.
        response (Response): The HTTP response object.
        current_user (AccessTokenData, optional): The current user's access token data. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        APIResponseBase: The API response containing the status and data.
    """

    csv_doc = UserDocumentQuery.get_user_document_by_id(db, document_id)

    if not csv_doc:
        logger.error("CSV document not found")
        response.status_code = status.HTTP_404_NOT_FOUND
        return APIResponseBase.not_found(message="CSV document not found")

    if str(csv_doc.customer_uuid) != current_user.uuid:
        logger.error("Unauthorized access")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return APIResponseBase.unauthorized(message="Unauthorized access")

    UserDocumentQuery.update_user_document(db, document_id, request.document_name)
    db.commit()

    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="CSV document updated successfully",
        data=UserDocumentUploadResponse(
            document_id=csv_doc.id,
            document_name=request.document_name,
            document_type=csv_doc.document_type,
        ),
    )


@router.delete("/{document_id}")
def delete_csv_document(
    document_id: int,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:
    """
    Deletes the CSV document with the given ID.

    Args:
        document_id (int): The ID of the CSV document to delete.
        response (Response): The HTTP response object.
        current_user (AccessTokenData, optional): The current user's access token data. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        APIResponseBase: The API response containing the status and data.
    """

    csv_doc = UserDocumentQuery.get_user_document_by_id(db, document_id)

    if not csv_doc:
        logger.error("CSV document not found")
        response.status_code = status.HTTP_404_NOT_FOUND
        return APIResponseBase.not_found(message="CSV document not found")

    if str(csv_doc.customer_uuid) != current_user.uuid:
        logger.error("Unauthorized access")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return APIResponseBase.unauthorized(message="Unauthorized access")

    chat_history = ChatHistoryQuery.get_chat_history(
        db, csv_doc.customer_uuid, "csv", csv_doc.id
    )
    if chat_history:
        ChatHistoryQuery.delete_chat_history_by_uuid(db, chat_history.uuid)
    UserDocumentQuery.delete_user_document(db, document_id)
    db.commit()

    # delete the file
    os.remove(csv_doc.document_url)

    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="CSV document deleted successfully",
        data=UserDocumentUploadResponse(
            document_id=csv_doc.id,
            document_name=csv_doc.document_name,
            document_type=csv_doc.document_type,
        ),
    )
