# app/api/v1.py
from fastapi import APIRouter
from app.api.endpoints import status

api_v1_router = APIRouter()

api_v1_router.include_router(status.router)