# app/modules/scheduling/routers.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import date
from typing import List
from .services import SchedulingService, get_scheduling_service
from .repository import ShiftRepository, get_shift_repository
from .models import ShiftAPI, AutoAssignShiftCreateAPI, AutoAssignResponseAPI
from app.core.security import CurrentUser, require_role
from app.modules.people.repository import UserRepository, get_user_repository

scheduling_router = APIRouter()

@scheduling_router.post(
    "/auto-assign",
    response_model=AutoAssignResponseAPI,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["admin", "manager"]))],
    summary="Create shift and auto-assign users",
    tags=["Scheduling - Admin"],
)
async def create_auto_assign_shift(
    shift_create_payload: AutoAssignShiftCreateAPI,
    current_user: CurrentUser = Depends(),
    scheduling_service: SchedulingService = Depends(get_scheduling_service),
    shift_repo: ShiftRepository = Depends(get_shift_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    created_shift = await scheduling_service.auto_assign_users_to_shift(
        shift_create_payload, shift_repo, user_repo, current_user
    )
    return created_shift

@scheduling_router.get(
    "/me",
    response_model=List[ShiftAPI],
    summary="Get my assigned shifts",
    tags=["Scheduling"],
)
async def get_my_shifts(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: CurrentUser = Depends(),
    scheduling_service: SchedulingService = Depends(get_scheduling_service),
    shift_repo: ShiftRepository = Depends(get_shift_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    return await scheduling_service.list_shifts_for_user(
        current_user.id, start_date, end_date, shift_repo, user_repo
    )