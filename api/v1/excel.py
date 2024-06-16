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
from schemas.user_documents import UserDocumentUploadResponse
from sqlalchemy.orm import Session
from config import Config
import random
from helper.openai import create_document_embedding


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
