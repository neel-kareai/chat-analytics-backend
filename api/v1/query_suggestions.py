from fastapi import APIRouter, status, Depends, Header, Response
from data_response.base_response import APIResponseBase
from db.queries.db_config import DBConfigQuery
from db.queries.user_documents import UserDocumentQuery
from db import get_db
from sqlalchemy.orm import Session
from helper.auth import AccessTokenData, get_current_user
from logger import logger
from helper.pipelines.suggestion import suggestion_pipeline
from schemas.ai_suggestion import AISuggestionRequest, AISuggestionResponse


router = APIRouter(prefix="/suggestion", tags=["suggestion"])


@router.post("/")
def get_suggestion_based_on_query(
    request: AISuggestionRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: AccessTokenData = Depends(get_current_user),
) -> APIResponseBase:
    """
    Get suggestions for a given query
    """
    data_source = None
    if request.query_type == "db":
        data_source = DBConfigQuery.get_db_config_by_id(db, request.data_source_id)
    elif request.query_type == "csv":
        data_source = UserDocumentQuery.get_user_document_by_id(
            db, request.data_source_id
        )

    if not data_source and request.data_source_id is not None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return APIResponseBase.error_response(
            message="Data source not found", status_code=status.HTTP_404_NOT_FOUND
        )

    if data_source:
        if str(data_source.customer_uuid) != current_user.uuid:
            response.status_code = status.HTTP_403_FORBIDDEN
            return APIResponseBase.error_response(
                message="Forbidden", status_code=status.HTTP_403_FORBIDDEN
            )

    suggestions = suggestion_pipeline(request, data_source)

    response.status_code = status.HTTP_200_OK
    return APIResponseBase.success_response(
        message="Suggestions fetched successfully",
        data=AISuggestionResponse(suggestions=suggestions),
    )
