from fastapi import APIRouter

from api.v1 import system
from api.v1 import customer
from api.v1 import db_operation

router = APIRouter()

router.include_router(system.router)
router.include_router(customer.router)
router.include_router(db_operation.router)
