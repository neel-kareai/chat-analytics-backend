from pydantic import BaseModel
from fastapi.responses import JSONResponse
from starlette import status
from typing import Any, Optional


class APIResponseBase(BaseModel):
    data: Optional[Any] = None
    message: Optional[str] = None
    # error: Optional[str] = None
    status_code: Optional[int] = None

    @classmethod
    def success_response(
        cls, data: Any = None, message: str = "Success", status_code: int = 200
    ):
        return cls(data=data, message=message, status_code=status_code)
    
    @classmethod
    def created(cls, data: Any = None, message: str = "Created"):
        return cls(data=data, message=message, status_code=status.HTTP_201_CREATED)

    @classmethod
    def bad_request(cls, message: str = "Bad Request"):
        return cls(status_code=status.HTTP_400_BAD_REQUEST, message=message)

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized"):
        return cls(status_code=status.HTTP_401_UNAUTHORIZED, message=message)

    @classmethod
    def forbidden(cls, message: str = "Forbidden"):
        return cls(status_code=status.HTTP_403_FORBIDDEN, message=message)

    @classmethod
    def not_found(cls, message: str = "Not Found"):
        return cls(status_code=status.HTTP_404_NOT_FOUND, message=message)

    @classmethod
    def internal_server_error(cls, message: str = "Internal Server Error"):
        return JSONResponse(
            content=cls(
                message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR).dict(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
