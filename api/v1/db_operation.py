from fastapi import APIRouter, status, Depends
from data_response.base_response import APIResponseBase
from data_class.db_config import (
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
        return APIResponseBase.internal_server_error(
            message="Failed to create db config"
        )

    db.commit()

    return APIResponseBase.created(
        message="DB config created successfully",
        data=NewDBCreateResponse(
            db_config_id=db_config.id,
            message="DB config created successfully"
        )
    )


@router.get("/")
async def get_db_config(db: Session = Depends(get_db),
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
        return APIResponseBase.not_found(
            message="DB config not found"
        )
    return APIResponseBase.success_response(
        message="DB config found",
        data=[db_config.to_dict() for db_config in db_configs]
    )
