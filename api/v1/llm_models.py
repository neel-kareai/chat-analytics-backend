from fastapi import APIRouter, status, Depends, Header, Response
from data_response.base_response import APIResponseBase
from logger import logger


router = APIRouter(prefix="/llm_models", tags=["llm_models"])


@router.get("/")
async def get_llm_models(response: Response) -> APIResponseBase:
    """
    Get all LLM models
    """
    llm_models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo-0125"]
    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="LLM models fetched successfully", data=llm_models
    )
