from fastapi import APIRouter, HTTPException, status
from data_response.base_response import APIResponseBase
from logger import logger

router = APIRouter(prefix="/system", tags=["system"])


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
