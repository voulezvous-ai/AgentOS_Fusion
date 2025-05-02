from bson import ObjectId
from typing import Optional, List, Dict, Any
from pymongo import DESCENDING
from loguru import logger
from app.core.database import BaseRepository
from .models import TransactionInDB, TransactionCreateInternal, TransactionUpdateInternal

class TransactionRepository(BaseRepository[TransactionInDB, TransactionCreateInternal, TransactionUpdateInternal]):
    async def get_by_ref(self, transaction_ref: str) -> Optional[TransactionInDB]:
        """Finds a transaction by its unique reference."""
        return await self.get_by({"transaction_ref": transaction_ref})

    async def list_by_user(
        self,
        user_id: ObjectId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionInDB]:
        """Lists transactions for a specific user, optionally filtered by date."""
        query: Dict[str, Any] = {"associated_user_id": user_id}
        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date

        return await self.list_by(query=query, skip=skip, limit=limit, sort=[("created_at", DESCENDING)])

# Factory to get repository instance
async def get_transaction_repository() -> TransactionRepository:
    return TransactionRepository(collection_name="transactions")