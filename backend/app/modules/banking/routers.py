from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request, status
from datetime import datetime
from typing import List, Optional
from loguru import logger
from .services import BankingService, get_banking_service
from .repository import TransactionRepository, get_transaction_repository
from .models import TransactionAPI, TransactionCreateAPI, RollbackPayloadAPI
from app.core.security import CurrentUser, require_role
from app.modules.people.services import UserService, get_user_service
from app.modules.people.repository import UserRepository, get_user_repository
from app.modules.office.services_audit import AuditService, get_audit_service
from app.core.counters import CounterService, get_counter_service

banking_router = APIRouter()

@banking_router.post(
    "/",
    response_model=TransactionAPI,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["admin", "finance"]))],
    summary="Manually record a financial transaction",
    tags=["Banking"]
)
async def record_manual_transaction_endpoint(
    transaction_in: TransactionCreateAPI,
    current_user: CurrentUser = Depends(),
    banking_service: BankingService = Depends(get_banking_service),
    banking_repo: TransactionRepository = Depends(get_transaction_repository),
    counter_service: CounterService = Depends(get_counter_service),
    audit_service: AuditService = Depends(get_audit_service),
    user_service: UserService = Depends(get_user_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    try:
        amount_dec = transaction_in._amount_decimal
        trx_internal = TransactionCreateInternal(
            type=transaction_in.type,
            amount=amount_dec,
            currency=transaction_in.currency,
            description=transaction_in.description,
            status=transaction_in.status or "completed",
            associated_user_id=transaction_in.associated_user_id,
            associated_order_id=transaction_in.associated_order_id,
            associated_shift_id=transaction_in.associated_shift_id,
            metadata=transaction_in.metadata
        )
        created_trx = await banking_service.record_transaction(
            transaction_in=trx_internal,
            banking_repo=banking_repo,
            counter_service=counter_service,
            audit_service=audit_service,
            user_service=user_service,
            user_repo=user_repo,
            actor=current_user,
            validate_balance=True
        )
        return TransactionAPI.model_validate(created_trx)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Failed to record manual transaction.")
        raise HTTPException(status_code=500, detail="Internal server error.")

@banking_router.post(
    "/{transaction_id}/rollback",
    response_model=TransactionAPI,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(["admin", "finance"]))],
    summary="Rollback a transaction",
    tags=["Banking"]
)
async def rollback_transaction_endpoint(
    transaction_id: str = Path(...),
    payload: RollbackPayloadAPI,
    current_user: CurrentUser = Depends(),
    banking_service: BankingService = Depends(get_banking_service),
    banking_repo: TransactionRepository = Depends(get_transaction_repository),
    counter_service: CounterService = Depends(get_counter_service),
    audit_service: AuditService = Depends(get_audit_service),
    user_service: UserService = Depends(get_user_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    try:
        rolled_back_trx = await banking_service.rollback_transaction(
            transaction_id_str=transaction_id,
            reason=payload.reason,
            actor=current_user,
            banking_repo=banking_repo,
            counter_service=counter_service,
            audit_service=audit_service,
            user_service=user_service,
            user_repo=user_repo
        )
        return TransactionAPI.model_validate(rolled_back_trx)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Failed to rollback transaction.")
        raise HTTPException(status_code=500, detail="Internal server error.")