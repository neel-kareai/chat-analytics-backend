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
from db.queries.chat_history import ChatHistoryQuery
from schemas.user_documents import UserDocumentUploadResponse, UserDocumentUpdateRequest
from sqlalchemy.orm import Session
from config import Config
import random
from helper.openai import create_document_embedding
import os

router = APIRouter(prefix="/excel", tags=["excel"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:

    logger.debug(f"Request: {file.filename}")

    # Check the file mime type
    if file.content_type not in [
        "application/vnd.ms-excel",
        "application/vnd.ms-excel.sheet.macroEnabled.12",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        logger.error("Invalid file type")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return APIResponseBase.bad_request(message="Invalid file type")

    # Save the file with
    filename = f"./tmp/{random.randbytes(8).hex()}.xlsx"
    with open(filename, "wb") as f:
        f.write(file.file.read())

    new_excel_doc = UserDocumentQuery.create_user_document(
        db, current_user.uuid, "excel", file.filename, filename, "processing"
    )

    if not new_excel_doc:
        logger.error("Failed to create excel document")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return APIResponseBase.internal_server_error(
            message="Failed to create excel document"
        )

    chat_history = ChatHistoryQuery.create_new_chat_history(
        db, current_user.uuid, "excel", new_excel_doc.id, new_excel_doc.document_name
    )

    db.commit()

    response.status_code = status.HTTP_201_CREATED
    return APIResponseBase.created(
        message="Excel file uploaded successfully",
        data=UserDocumentUploadResponse(
            document_id=new_excel_doc.id,
            document_name=new_excel_doc.document_name,
            document_type=new_excel_doc.document_type,
        ),
    )


@router.get("/{document_id}")
async def get_excel_document(
    document_id: int,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:
    """
    Get the Excel document by its ID.

    Args:
        document_id (int): The ID of the document to get.
        response (Response): The response object to be returned.
        current_user (AccessTokenData, optional): The current user's access token data. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        APIResponseBase: The API response containing the document data.
    """
    excel_doc = UserDocumentQuery.get_user_document_by_id(db, document_id, "excel")
    if not excel_doc:
        logger.error("Excel document not found")
        response.status_code = status.HTTP_404_NOT_FOUND
        return APIResponseBase.not_found(message="Excel document not found")

    if str(excel_doc.customer_uuid) != current_user.uuid:
        logger.error("Unauthorized access")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return APIResponseBase.unauthorized(message="Unauthorized access")

    return APIResponseBase.success_response(
        message="Excel document found",
        data=UserDocumentUploadResponse(
            document_id=excel_doc.id,
            document_name=excel_doc.document_name,
            document_type=excel_doc.document_type,
        ),
    )


@router.put("/{document_id}")
async def update_excel_document(
    document_id: int,
    request: UserDocumentUpdateRequest,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:
    """
    Update the Excel document by its ID.

    Args:
        document_id (int): The ID of the document to update.
        request (UserDocumentUpdateRequest): The request object containing the new document details.
        response (Response): The response object to be returned.
        current_user (AccessTokenData, optional): The current user's access token data. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        APIResponseBase: The API response containing the updated document data.
    """
    excel_doc = UserDocumentQuery.get_user_document_by_id(db, document_id, "excel")
    if not excel_doc:
        logger.error("Excel document not found")
        response.status_code = status.HTTP_404_NOT_FOUND
        return APIResponseBase.not_found(message="Excel document not found")

    if str(excel_doc.customer_uuid) != current_user.uuid:
        logger.error("Unauthorized access")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return APIResponseBase.unauthorized(message="Unauthorized access")

    excel_doc = UserDocumentQuery.update_user_document(
        db, document_id, request.document_name
    )

    db.commit()

    return APIResponseBase.success_response(
        message="Excel document updated",
        data=excel_doc.to_dict(),
    )


@router.delete("/{document_id}")
async def delete_excel_document(
    document_id: int,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:
    """
    Delete the Excel document by its ID.

    Args:
        document_id (int): The ID of the document to delete.
        response (Response): The response object to be returned.
        current_user (AccessTokenData, optional): The current user's access token data. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        APIResponseBase: The API response containing the status.
    """
    excel_doc = UserDocumentQuery.get_user_document_by_id(db, document_id, "excel")
    if not excel_doc:
        logger.error("Excel document not found")
        response.status_code = status.HTTP_404_NOT_FOUND
        return APIResponseBase.not_found(message="Excel document not found")

    if str(excel_doc.customer_uuid) != current_user.uuid:
        logger.error("Unauthorized access")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return APIResponseBase.unauthorized(message="Unauthorized access")

    chat_history = ChatHistoryQuery.get_chat_history(
        db, current_user.uuid, "excel", excel_doc.id
    )
    if chat_history:
        ChatHistoryQuery.delete_chat_history_by_uuid(db, chat_history.uuid)
    UserDocumentQuery.delete_user_document(db, document_id)
    db.commit()

    # Delete the file
    os.remove(excel_doc.document_url)

    return APIResponseBase.success_response(
        message="Excel document deleted",
    )
