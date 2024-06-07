from fastapi import APIRouter
from data_response.base_response import APIResponseBase
from logger import logger


from api.v1 import customer
from api.v1 import db_operation

router = APIRouter()

router.include_router(customer.router, prefix="/v1")
router.include_router(db_operation.router, prefix="/v1")


@router.get("/health")
async def get_system_health() -> APIResponseBase:
    """
        Check the health of the system
    """
    logger.info("Checking system health")
    # health logic will be added later here
    logger.info("System is healthy")

    return APIResponseBase.success_response(
        message="System is healthy",
        data={"status": "UP"}
    )
