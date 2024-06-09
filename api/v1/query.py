from fastapi import APIRouter, status, Depends, Response
from data_response.base_response import APIResponseBase
from helper.auth import AccessTokenData, get_current_user
from schemas.query import CustomerQueryRequest, CustomerQueryResponse
from db.queries.db_config import DBConfigQuery
from db.queries.user_documents import UserDocumentQuery
from db import get_db
from sqlalchemy.orm import Session
from logger import logger
from helper.db_query import db_config_pipeline
from helper.csv_query import csv_pipeline


router = APIRouter(prefix="/query", tags=["query"])


@router.post("/{query_type}")
async def query(query_type: str,
                request: CustomerQueryRequest,
                response: Response,
                current_user: AccessTokenData = Depends(get_current_user),
                db: Session = Depends(get_db)
                ) -> APIResponseBase:
    """
        Query the database or csv file
    """

    logger.debug(f"Using LLM : {request.model}")

    result = None

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

    elif query_type == "db":
        logger.debug(f"Received query for DB")

        db_config = DBConfigQuery.get_db_config_by_id(db, request.data_source_id)
        if not db_config:
            logger.error("DB not found")
            return APIResponseBase.bad_request(
                message="DB not found"
            )
        
        if str(db_config.customer_uuid) != current_user.uuid:
            logger.error("Unauthorized access")
            return APIResponseBase.unauthorized(
                message="Unauthorized access"
            )
        try:
            result, sql_query = db_config_pipeline(
                db_config.db_type,
                db_config.db_config, request.query, request.model
            )
        except Exception as e:
            logger.error(f"Failed to query db: {e}")
            return APIResponseBase.internal_server_error(
                message="Failed to query db. Please check your query and try again."
            )

    else:
        logger.error("Invalid query type")
        return APIResponseBase.bad_request(
            message="Invalid query type"
        )

    return APIResponseBase.success_response(
        message="Query successful",
        data=CustomerQueryResponse(
            query=request.query,
            response=result,
            sql_query=sql_query if query_type == "db" else None,
            data_source_id=request.data_source_id
        )
    )
