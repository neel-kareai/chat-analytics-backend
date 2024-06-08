from fastapi import APIRouter, status, Depends, Header
from data_response.base_response import APIResponseBase
from schemas.customer import (
    CustomerLoginRequest,
    CustomerLoginResponse,
    CustomerRegisterRequest,
    CustomerRegisterResponse,
)
from helper.auth import JWTHandler, RefreshTokenData
from db import get_db
from sqlalchemy.orm import Session
from db.queries.customer import CustomerQuery
from logger import logger
import re

router = APIRouter(prefix="/customer", tags=["customer"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_customer(
    request: CustomerRegisterRequest, db: Session = Depends(get_db)
) -> APIResponseBase:
    """
    Register a new customer
    """

    customer = CustomerQuery.get_customer_by_email(db, request.email)
    if customer:
        logger.error("Customer with this email already exists")
        return APIResponseBase.bad_request(
            message="Customer with this email already exists"
        )

    customer = CustomerQuery.create_customer(
        db, request.name, request.email, request.password
    )

    if not customer:
        logger.error("Failed to create customer")
        return APIResponseBase.internal_server_error(
            message="Failed to create customer"
        )

    db.commit()

    return APIResponseBase.created(
        message="Customer created successfully",
    )


@router.post("/login")
async def login_customer(
    request: CustomerLoginRequest, db: Session = Depends(get_db)
) -> APIResponseBase:
    """
    Login a customer
    """

    customer = CustomerQuery.get_customer_by_email_password(
        db, request.email, request.password
    )

    if not customer:
        logger.error("Invalid email or password")
        return APIResponseBase.unauthorized(message="Invalid email or password")

    access_token_data = {
        "uuid": str(customer.uuid),
        "email": customer.email,
        "name": customer.name,
    }
    refresh_token_data = {
        "uuid": str(customer.uuid),
    }

    access_token = JWTHandler.create_access_token(access_token_data)
    refresh_token = JWTHandler.create_refresh_token(refresh_token_data)

    # update last login
    CustomerQuery.update_customer_last_login(db, customer)

    return APIResponseBase.success_response(
        data=CustomerLoginResponse(
            access_token=access_token, refresh_token=refresh_token
        ).model_dump(),
        message="Login successful",
    )


@router.post("/refresh-token")
async def refresh_access_token(
    authorization: str = Header(None), db: Session = Depends(get_db)
) -> APIResponseBase:
    """
    Refresh access token
    """

    if not authorization:
        logger.error("Authorization header is missing")
        return APIResponseBase.bad_request(message="Authorization header is missing")

    # extract token from header
    refresh_token = re.sub(r"Bearer ", "", authorization)

    refresh_token_decoded: RefreshTokenData = JWTHandler.decode_refresh_token(
        refresh_token
    )
    if not refresh_token_decoded:
        logger.error("Invalid refresh token")
        return APIResponseBase.bad_request(message="Invalid refresh token")

    customer = CustomerQuery.get_customer_by_uuid(db, refresh_token_decoded.uuid)
    if not customer:
        logger.error("Customer not found")
        return APIResponseBase.not_found(message="Customer not found")

    access_token_data = {
        "uuid": str(customer.uuid),
        "email": customer.email,
        "name": customer.name,
    }

    access_token = JWTHandler.create_access_token(access_token_data)

    return APIResponseBase.success_response(
        data=CustomerLoginResponse(
            access_token=access_token, refresh_token=refresh_token
        ).model_dump(),
        message="Access token refreshed successfully",
    )
