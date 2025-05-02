# app/modules/scheduling/repository.py
from pymongo.results import UpdateResult
from datetime import datetime, date, time
from typing import List, Optional
from bson import ObjectId
from loguru import logger
from app.core.database import BaseRepository
from .models import ShiftInDB, ShiftCreateInternal, ShiftUpdateInternal, UserAssignment

class ShiftRepository(BaseRepository[ShiftInDB, ShiftCreateInternal, ShiftUpdateInternal]):
    async def create_indexes(self):
        await self.collection.create_index("shift_date")
        await self.collection.create_index("assigned_users.user_id")

    async def list_shifts_by_user_and_date(
        self,
        user_id: ObjectId,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 31,
    ) -> List[ShiftInDB]:
        query = {
            "assigned_users.user_id": user_id,
            "shift_date": {"$gte": start_date, "$lte": end_date},
        }
        sort_order = [("shift_date", 1), ("start_time", 1)]
        return await self.list_by(query=query, skip=skip, limit=limit, sort=sort_order)

    async def check_user_already_assigned(
        self, user_id: ObjectId, shift_date: date, start_time: time, end_time: time
    ) -> bool:
        query = {"assigned_users.user_id": user_id, "shift_date": shift_date}
        count = await self.collection.count_documents(query)
        return count > 0

    async def add_assigned_users_to_shift(
        self, shift_id: ObjectId, assignments: List[UserAssignment]
    ) -> bool:
        if not assignments:
            return False
        log = logger.bind(shift_id=str(shift_id), assign_count=len(assignments))
        log.info("Adding assigned users to shift...")
        user_assignment_dicts = [a.model_dump(mode="json") for a in assignments]
        try:
            result: UpdateResult = await self.collection.update_one(
                {"_id": shift_id},
                {
                    "$push": {"assigned_users": {"$each": user_assignment_dicts}},
                    "$set": {"status": "assigned", "updated_at": datetime.utcnow()},
                },
            )
            success = result.modified_count > 0
            if success:
                log.success("Users added to shift assignment.")
            else:
                log.warning("Failed to add users to shift.")
            return success
        except Exception as e:
            self._handle_db_exception(e, "add_assigned_users_to_shift", shift_id)
            return False

# Factory to get repository instance
async def get_shift_repository() -> ShiftRepository:
    return ShiftRepository(collection_name="shifts")