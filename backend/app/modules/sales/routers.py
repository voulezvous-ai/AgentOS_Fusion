from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional

from app.core.security import CurrentUser, UserInDB # Assuming CurrentUser provides UserInDB
from app.models.sales import OrderAPI, OrderCreateAPI, OrderStatusUpdateAPI # API Models
from app.modules.office.services_audit import AuditService, get_audit_service
from app.modules.people.repository import UserRepository, get_user_repository
from app.core.counters import CounterService, get_counter_service
from .repository import OrderRepository, get_order_repository, ProductRepository, get_product_repository
from .services import OrderService, get_order_service # Renamed from get_sales_service
from .reservation_service import StockReservationService, get_reservation_service # Assuming exists
from loguru import logger

# --- Router ---
orders_router = APIRouter()

@orders_router.post(
    "/",
    response_model=OrderAPI,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    tags=["Sales - Orders"]
    # No specific role required? Any logged-in user can create an order.
)
async def create_order_endpoint(
    request: Request, # For audit logging
    order_in: OrderCreateAPI, # API Payload model
    current_user: CurrentUser = Depends(), # The customer/user placing the order
    order_service: OrderService = Depends(get_order_service),
    order_repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    counter_service: CounterService = Depends(get_counter_service),
    reservation_service: StockReservationService = Depends(get_reservation_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Creates a new sales order. Requires product IDs and quantities.
    Processes items, calculates total, reserves stock, and saves the order.
    """
    log = logger.bind(user_id=str(current_user.id), channel=order_in.channel)
    log.info("Endpoint: Creating new order...")
    try:
        # Service handles validation, stock reservation, DB creation, and potential rollbacks
        created_order_db = await order_service.create_order(
            order_in=order_in,
            creator=current_user, # Pass the logged-in user as the creator/customer
            order_repo=order_repo,
            product_repo=product_repo,
            user_repo=user_repo,
            counter_service=counter_service,
            reservation_service=reservation_service,
            audit_service=audit_service, # Pass for internal service logging if needed
        )

        # Log successful creation audit event at the endpoint level
        await audit_service.log_audit_event(
            action="order_created", status="success", entity_type="Order",
            entity_id=created_order_db.id, audit_repo=None, # Use service's repo
            details={"order_ref": created_order_db.order_ref, "total": str(created_order_db.total_amount), "channel": created_order_db.channel},
            current_user=current_user, request=request
        )

        # Convert internal DB model to API model for response
        # Service might return DB model, endpoint converts
        # Or service could return API model directly (less clean separation)
        # Assuming service returns DB model for now
        order_api = await order_service.get_order(str(created_order_db.id), order_repo, user_repo) # Use get_order to enrich
        if not order_api: # Should not happen if creation succeeded
            raise HTTPException(status_code=500, detail="Order created but failed to retrieve for response.")

        return order_api

    except HTTPException as http_exc:
        # Log failure audit event for anticipated errors (4xx)
        log.warning(f"Failed to create order: {http_exc.detail} (Status: {http_exc.status_code})")
        await audit_service.log_audit_event(
            action="order_create_failed", status="failure", entity_type="Order",
            error_message=http_exc.detail, audit_repo=None,
            details=order_in.model_dump(), # Log input payload on failure
            current_user=current_user, request=request
        )
        raise http_exc # Re-raise the exception
    except Exception as e:
        # Log failure audit event for unexpected errors (5xx)
        log.exception(f"Unexpected error creating order: {e}")
        await audit_service.log_audit_event(
            action="order_create_failed", status="failure", entity_type="Order",
            error_message=f"Unexpected error: {e}", audit_repo=None,
            details=order_in.model_dump(),
            current_user=current_user, request=request
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error creating order.")

# Add other order endpoints (GET /, GET /{id}, PATCH /{id}/status, etc.) here...
# ...