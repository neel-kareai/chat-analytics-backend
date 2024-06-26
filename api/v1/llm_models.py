from fastapi import APIRouter, status, Depends, Header, Response
from data_response.base_response import APIResponseBase
from logger import logger
from config import Config

router = APIRouter(prefix="/llm_models", tags=["llm_models"])


@router.get("/")
async def get_llm_models(response: Response) -> APIResponseBase:
    """
    Retrieves the list of LLM models.

    Args:
        response (Response): The response object.

    Returns:
        APIResponseBase: The API response containing the list of LLM models.
    """
    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="LLM models fetched successfully",
        data={
            "default_llm_model": Config.DEFAULT_LLM_MODEL,
            "llm_models": {
                "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo-0125"],
                "google": ["gemini-1.5-pro", "gemini-1.5-flash"],
                "anthropic": [
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                ],
            },
        },
    )
