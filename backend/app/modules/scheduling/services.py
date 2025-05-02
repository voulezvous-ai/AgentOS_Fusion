# app/modules/scheduling/services.py
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from fastapi import HTTPException, status
from loguru import logger
from .repository import ShiftRepository
from .models import (
    ShiftInDB,
    ShiftCreateInternal,
    UserAssignment,
    ShiftAPI,
    AssignedUserAPI,
)
from app.modules.people.repository import UserRepository
from app.modules.banking.services import BankingService
from app.modules.banking.repository import TransactionRepository
from app.core.counters import CounterService

class SchedulingService:
    async def _enrich_shift(self, shift_db: ShiftInDB, user_repo: UserRepository) -> ShiftAPI:
        shift_api = ShiftAPI(
            id=str(shift_db.id),
            shift_date=shift_db.shift_date,
            start_time=shift_db.start_time,
            end_time=shift_db.end_time,
            required_role=shift_db.required_role,
            max_participants=shift_db.max_participants,
            required_balance=str(shift_db.required_balance),
            status=shift_db.status,
            notes=shift_db.notes,
            assigned_users=[],
            assigned_count=len(shift_db.assigned_users),
            created_at=shift_db.created_at,
            updated_at=shift_db.updated_at,
        )

        assigned_user_ids = [ua.user_id for ua in shift_db.assigned_users]
        if assigned_user_ids:
            users = await user_repo.list_by({"_id": {"$in": assigned_user_ids}}, limit=0)
            user_map = {str(u.id): u for u in users}
            enriched_assignments = []
            for ua in shift_db.assigned_users:
                user = user_map.get(str(ua.user_id))
                enriched_assignments.append(
                    AssignedUserAPI(
                        user_id=str(ua.user_id),
                        user_name=f"{user.profile.first_name or ''} {user.profile.last_name or ''}".strip()
                        if user and user.profile
                        else "Unknown User",
                    )
                )
            shift_api.assigned_users = enriched_assignments

        return shift_api

    async def list_shifts_for_user(
        self,
        user_id: ObjectId,
        start_date: date,
        end_date: date,
        shift_repo: ShiftRepository,
        user_repo: UserRepository,
        skip: int = 0,
        limit: int = 31,
    ) -> List[ShiftAPI]:
        log = logger.bind(service="SchedulingService", user_id=str(user_id))
        log.debug("Listing assigned shifts for user...")
        shifts_db = await shift_repo.list_shifts_by_user_and_date(
            user_id, start_date, end_date, skip, limit
        )
        enriched_shifts = [await self._enrich_shift(s, user_repo) for s in shifts_db]
        log.info(f"Found {len(enriched_shifts)} assigned shifts for user.")
        return enriched_shifts

    async def auto_assign_users_to_shift(
        self,
        shift: ShiftInDB,
        shift_repo: ShiftRepository,
        user_repo: UserRepository,
        banking_service: BankingService,
        banking_repo: TransactionRepository,
        counter_service: CounterService,
    ) -> Tuple[int, List[ObjectId]]:
        log = logger.bind(service="SchedulingService", shift_id=str(shift.id))
        log.info("Starting auto-assignment...")
        slots_to_fill = shift.max_participants
        assignments = []
        assigned_user_ids = []

        query = {"is_active": True, "profile.balance": {"$gte": str(shift.required_balance)}}
        if shift.required_role:
            query["roles"] = shift.required_role

        sort_criteria = [("created_at", 1)]
        eligible_users_cursor = user_repo.collection.find(query).sort(sort_criteria)

        async for user_doc in eligible_users_cursor:
            if len(assignments) >= slots_to_fill:
                break

            user = await user_repo.model_validate(user_doc)
            user_id = user.id
            log.debug(f"Checking user {user.email}...")

            is_already_assigned = await shift_repo.check_user_already_assigned(
                user_id, shift.shift_date, shift.start_time, shift.end_time
            )
            if is_already_assigned:
                log.debug(f"User {user.email} already assigned. Skipping.")
                continue

            assignments.append(UserAssignment(user_id=user_id))
            assigned_user_ids.append(user_id)

        if assignments:
            success = await shift_repo.add_assigned_users_to_shift(shift.id, assignments)
            if not success:
                log.error("Failed to update shift with assignments.")
        return len(assignments), assigned_user_ids

# Factory to get service instance
async def get_scheduling_service() -> SchedulingService:
    return SchedulingService()