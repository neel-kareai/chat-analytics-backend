from fastapi import APIRouter, status, Depends, Response
from data_response.base_response import APIResponseBase
from helper.auth import AccessTokenData, get_current_user
from schemas.query import CustomerQueryRequest, CustomerQueryResponse
from db.queries.db_config import DBConfigQuery
from db.queries.user_documents import UserDocumentQuery
from db.queries.chat_history import ChatHistoryQuery
from db import get_db
from sqlalchemy.orm import Session
from logger import logger
from helper.pipelines.db_query import db_config_pipeline
from helper.pipelines.csv_query import csv_pipeline
from helper.pipelines.excel_query import excel_pipeline
from helper.pipelines.simple_chat import simple_chat_pipeline


router = APIRouter(prefix="/query", tags=["query"])


@router.post("/{query_type}")
async def query(
    query_type: str,
    request: CustomerQueryRequest,
    response: Response,
    current_user: AccessTokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponseBase:
    """
    Executes a query based on the provided query type.

    Args:
        query_type (str): The type of query to execute. Can be "csv" or "db".
        request (CustomerQueryRequest): The request object containing the query details.
        response (Response): The response object to be returned.
        current_user (AccessTokenData, optional): The current user's access token data. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        APIResponseBase: The API response containing the query result.
    """
    logger.debug(f"Using LLM : {request.model}")

    result = None
    sql_query = None
    if request.chat_uuid is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return APIResponseBase.bad_request(message="chat_uuid is required")

    if not ChatHistoryQuery.is_valid_chat_history(
        db,
        str(request.chat_uuid),
        query_type,
        current_user.uuid,
        request.data_source_id,
    ):
        logger.error("Invalid chat history")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return APIResponseBase.bad_request(message="Invalid chat uuid")

    if query_type == "csv":
        logger.debug(f"Received query for CSV")

        # Depreciate this case
        response.status_code = status.HTTP_400_BAD_REQUEST
        return APIResponseBase.bad_request(
            message="This API is deprecated. Please use v2 API"
        )
        # csv_file = UserDocumentQuery.get_user_document_by_id(
        #     db, request.csv_file_id)
        # if not csv_file:
        #     logger.error("CSV file not found")
        #     return APIResponseBase.bad_request(
        #         message="CSV file not found"
        #     )

        # if str(csv_file.customer_uuid) != current_user.uuid:
        #     logger.error("Unauthorized access")
        #     return APIResponseBase.unauthorized(
        #         message="Unauthorized access"
        #     )

        # # check if the document is embedded or not
        # if csv_file.is_embedded is None or csv_file.is_embedded is False:
        #     logger.debug("Embedding is still in progress")
        #     return APIResponseBase.bad_request(
        #         message="document is still being processed"
        #     )

        # result = csv_pipeline(csv_file.embed_url, request.query)
    elif query_type == "excel":
        logger.debug(f"Received query for Excel")

        excel_file = UserDocumentQuery.get_user_document_by_id(
            db, request.data_source_id
        )
        if not excel_file:
            logger.error("Excel file not found")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return APIResponseBase.bad_request(message="Excel file not found")

        if str(excel_file.customer_uuid) != current_user.uuid:
            logger.error("Unauthorized access")
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return APIResponseBase.unauthorized(message="Unauthorized access")

        result = excel_pipeline(
            excel_file.document_url,
            request.query,
            str(request.chat_uuid),
            request.model,
        )
    elif query_type == "db":
        logger.debug(f"Received query for DB")

        db_config = DBConfigQuery.get_db_config_by_id(db, request.data_source_id)
        if not db_config:
            logger.error("DB not found")
            return APIResponseBase.bad_request(message="DB not found")

        if str(db_config.customer_uuid) != current_user.uuid:
            logger.error("Unauthorized access")
            return APIResponseBase.unauthorized(message="Unauthorized access")
        try:
            result, sql_query = db_config_pipeline(
                db_config.db_type,
                db_config.db_config,
                request.query,
                str(request.chat_uuid),
                request.model,
            )
        except Exception as e:
            logger.error(f"Failed to query db: {e}")
            return APIResponseBase.internal_server_error(
                message="Failed to query db. Please check your query and try again."
            )
    else:
        logger.error("Invalid query type")
        return APIResponseBase.bad_request(message="Invalid query type")

    return APIResponseBase.success_response(
        message="Query successful",
        data=CustomerQueryResponse(
            query=request.query,
            response=result,
            sql_query=sql_query if query_type == "db" else None,
            data_source_id=request.data_source_id,
            chat_uuid=str(request.chat_uuid),
        ),
    )


@router.post("/")
def chat(
    request: CustomerQueryRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: AccessTokenData = Depends(get_current_user),
) -> APIResponseBase:
    """
    Process a chat request and generate a response.

    Args:
        request (CustomerQueryRequest): The customer query request object.
        response (Response): The response object.
        current_user (AccessTokenData, optional): The current user access token data. Defaults to Depends(get_current_user).

    Returns:
        APIResponseBase: The API response containing the chat result.
    """
    logger.debug(f"Received chat request")
    chat_uuid = None
    if request.chat_uuid is None:
        # create new chat history
        chat_history = ChatHistoryQuery.create_new_chat_history(
            db, current_user.uuid, "chat", request.data_source_id, request.query[:100]
        )
        db.commit()
        chat_uuid = str(chat_history.uuid)
    else:
        chat_uuid = str(request.chat_uuid)

    result = simple_chat_pipeline(request.query, chat_uuid, request.model)

    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="Chat successful",
        data=CustomerQueryResponse(
            query=request.query,
            response=result,
            chat_uuid=chat_uuid,
        ),
    )
