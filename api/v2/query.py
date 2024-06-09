from fastapi import APIRouter, status, Depends, Response
from data_response.base_response import APIResponseBase
from helper.auth import AccessTokenData, get_current_user
from schemas.query import CustomerQueryRequest, CustomerQueryResponse
from db.queries.user_documents import UserDocumentQuery
from db import get_db
from sqlalchemy.orm import Session
from logger import logger
from helper.csv_query import csv_pipeline_v2


router = APIRouter(prefix="/query", tags=["query"])


@router.post("/{query_type}")
async def query(query_type: str,
                request: CustomerQueryRequest,
                response: Response,
                current_user: AccessTokenData = Depends(get_current_user),
                db: Session = Depends(get_db)
                ) -> APIResponseBase:
    """
        Query the database or csv file using
        Llama's Query Pipeline module without any need of
        embeddings
    """
    logger.debug(f"Using LLM : {request.model}")
    result = None

    if query_type == "csv":
        logger.debug(f"Received query for CSV")

        csv_file = UserDocumentQuery.get_user_document_by_id(
            db, request.data_source_id)
        if not csv_file:
            logger.error("CSV file not found")
            return APIResponseBase.bad_request(
                message="CSV file not found"
            )
        
        if str(csv_file.customer_uuid) != current_user.uuid:
            logger.error("Unauthorized access")
            return APIResponseBase.unauthorized(
                message="Unauthorized access"
            )
        

        result = csv_pipeline_v2(csv_file.document_url, request.query)

    else:
        # bad request
        response.status_code = status.HTTP_400_BAD_REQUEST
        return APIResponseBase.bad_request(
            message="Invalid query type"
        )


    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="Query successful",
        data=CustomerQueryResponse(
            query=request.query,
            response=result,
            data_source_id=request.data_source_id if query_type == "csv" else None
        )
    )
