from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from fastapi import HTTPException, status
from loguru import logger
from .repository import TransactionRepository
from .models import TransactionInDB, TransactionCreateInternal, TRANSACTION_TYPES, TRANSACTION_STATUSES
from app.modules.people.services import UserService
from app.modules.people.repository import UserRepository
from app.modules.office.services_audit import AuditService
from app.core.counters import CounterService

class BankingService:
    def _get_balance_change_sign(self, transaction_type: TRANSACTION_TYPES) -> int:
        if transaction_type in ["payment_received", "bonus_income", "other_income", "correction"]:
            return 1
        elif transaction_type in ["sale_income", "shift_fee", "refund_outgoing", "manual_adjustment", "commission_payout", "other_expense"]:
            return -1
        else:
            return 0

    async def record_transaction(
        self,
        transaction_in: TransactionCreateInternal,
        banking_repo: TransactionRepository,
        counter_service: CounterService,
        audit_service: AuditService,
        user_service: UserService,
        user_repo: UserRepository,
        actor: Optional[UserInDB] = None,
        validate_balance: bool = True
    ) -> TransactionInDB:
        log = logger.bind(service="BankingService", type=transaction_in.type)
        log.info("Recording transaction...")

        if transaction_in.amount <= Decimal("0.00"):
            raise ValueError("Transaction amount must be positive.")

        balance_sign = self._get_balance_change_sign(transaction_in.type)
        balance_adjustment = transaction_in.amount * balance_sign

        target_user_id = transaction_in.associated_user_id

        if target_user_id and balance_adjustment < Decimal("0.00") and validate_balance:
            current_balance = await user_service.get_customer_balance(str(target_user_id), user_repo)
            if current_balance + balance_adjustment < Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient balance. Required: {-balance_adjustment}, Available: {current_balance}"
                )

        trx_ref = await counter_service.generate_reference("TRX")
        trx_data = transaction_in.model_dump()
        trx_data["transaction_ref"] = trx_ref
        for key in ["associated_user_id", "associated_order_id", "associated_shift_id"]:
            if trx_data.get(key):
                trx_data[key] = banking_repo._to_objectid(trx_data[key])

        created_trx_db = await banking_repo.create(trx_data)

        if created_trx_db.status == "completed" and target_user_id and balance_adjustment != Decimal("0.00"):
            await user_service.adjust_customer_balance(
                user_id=target_user_id,
                amount_change_decimal=balance_adjustment,
                reason=f"Transaction {trx_ref}: {created_trx_db.description}",
                actor=actor,
                user_repo=user_repo,
                audit_service=audit_service,
                order_ref=str(created_trx_db.associated_order_id) if created_trx_db.associated_order_id else None
            )

        await audit_service.log_audit_event(
            action="transaction_recorded",
            status="success",
            entity_type="Transaction",
            entity_id=created_trx_db.id,
            details=created_trx_db.model_dump(),
            current_user=actor
        )
        return created_trx_db

    async def rollback_transaction(
        self,
        transaction_id_str: str,
        reason: str,
        actor: UserInDB,
        banking_repo: TransactionRepository,
        counter_service: CounterService,
        audit_service: AuditService,
        user_service: UserService,
        user_repo: UserRepository
    ) -> TransactionInDB:
        log = logger.bind(service="BankingService", transaction_id=transaction_id_str)
        log.info("Rolling back transaction...")

        original_trx = await banking_repo.get_by_id(transaction_id_str)
        if not original_trx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

        if original_trx.status == "rolled_back":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction has already been rolled back.")
        if original_trx.status != "completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot rollback transaction with status '{original_trx.status}'.")

        original_balance_sign = self._get_balance_change_sign(original_trx.type)
        balance_reversal_amount = original_trx.amount * original_balance_sign * -1

        correction_create = TransactionCreateInternal(
            type="correction",
            amount=abs(balance_reversal_amount),
            currency=original_trx.currency,
            description=f"Correction for rollback of {original_trx.transaction_ref}. Reason: {reason}",
            status="completed",
            associated_user_id=original_trx.associated_user_id,
            metadata={"correction_for_trx_ref": original_trx.transaction_ref}
        )

        correction_trx = await self.record_transaction(
            transaction_in=correction_create,
            banking_repo=banking_repo,
            counter_service=counter_service,
            audit_service=audit_service,
            user_service=user_service,
            user_repo=user_repo,
            actor=actor,
            validate_balance=False
        )

        update_data = TransactionUpdateInternal(
            status="rolled_back",
            rollback_reason=reason,
            rolled_back_by_trx_ref=correction_trx.transaction_ref
        )
        await banking_repo.update(original_trx.id, update_data)

        await audit_service.log_audit_event(
            action="transaction_rolled_back",
            status="success",
            entity_type="Transaction",
            entity_id=original_trx.id,
            details={"reason": reason, "correction_trx_ref": correction_trx.transaction_ref},
            current_user=actor
        )
        return original_trx

# Factory to get service instance
async def get_banking_service() -> BankingService:
    return BankingService()