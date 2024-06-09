from fastapi import APIRouter, status, Depends, Response
from data_response.base_response import APIResponseBase
from schemas.db_config import (
    NewDBCreateRequest,
    NewDBCreateResponse,
)
from helper.auth import JWTHandler, AccessTokenData, get_current_user
from db import get_db
from sqlalchemy.orm import Session
from db.queries.db_config import DBConfigQuery
from logger import logger

router = APIRouter(prefix="/db-operation", tags=["db_operation"])


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_new_db(request: NewDBCreateRequest,
                        response: Response,
                        db: Session = Depends(get_db),
                        current_user: AccessTokenData = Depends(
                            get_current_user)
                        ) -> APIResponseBase:
    """
        Create a new database config
    """
    logger.debug(f"Request: {request}")
    db_config = DBConfigQuery.create_db_config(
        db, current_user.uuid, request.db_type, request.db_config
    )

    if not db_config:
        logger.error("Failed to create db config")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return APIResponseBase.internal_server_error(
            message="Failed to create db config"
        )

    db.commit()

    response.status_code = status.HTTP_201_CREATED
    return APIResponseBase.created(
        message="DB config created successfully",
        data=NewDBCreateResponse(
            db_config_id=db_config.id,
            message="DB config created successfully"
        )
    )


@router.get("/")
async def get_db_config(response: Response,
    db: Session = Depends(get_db),
                        current_user: AccessTokenData = Depends(
                            get_current_user)
                        ) -> APIResponseBase:
    """
        Get database config
    """

    db_configs = DBConfigQuery.get_db_config_by_customer_uuid(
        db, current_user.uuid)

    if not db_configs:
        logger.error("DB config not found")
        response.status_code = status.HTTP_404_NOT_FOUND
        return APIResponseBase.not_found(
            message="DB config not found"
        )
    
    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="DB config found",
        data={
            "db_configs": [db_config.to_dict() for db_config in db_configs],
            "customer_uuid": current_user.uuid
        },
    )
