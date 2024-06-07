from fastapi import APIRouter, status, Depends
from data_response.base_response import APIResponseBase
from helper.auth import AccessTokenData, get_current_user
from schemas.query import CustomerQueryRequest
from db.queries.db_config import DBConfigQuery
from db import get_db
from sqlalchemy.orm import Session
from logger import logger
from helper.db_query import db_config_pipeline


router = APIRouter(prefix="/query", tags=["query"])


@router.post("/{query_type}")
async def query(query_type: str,
                request: CustomerQueryRequest,
                current_user: AccessTokenData = Depends(get_current_user),
                db: Session = Depends(get_db)
                ) -> APIResponseBase:
    """
        Query the database
    """

    response = None

    if query_type == "csv":
        logger.debug(f"Received query for CSV")

    elif query_type == "db":
        logger.debug(f"Received query for DB")

        db_config = DBConfigQuery.get_db_config_by_id(db, request.db_id)
        if not db_config:
            logger.error("DB not found")
            return APIResponseBase.bad_request(
                message="DB not found"
            )
        
        response = db_config_pipeline(
            db_config.db_type,
            db_config.db_config, request.query
        )

    else:
        logger.error("Invalid query type")
        return APIResponseBase.bad_request(
            message="Invalid query type"
        )

    return APIResponseBase.success_response(
        message="Query successful",
        data={
            "query": request.query,
            "db_id": request.db_id,
            "csv_file_id": request.csv_file_id,
            "response": response
        }
    )
