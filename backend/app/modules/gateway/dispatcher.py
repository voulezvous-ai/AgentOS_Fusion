# ... (other imports: logger, HTTPException, services, repos, models) ...
from .models import GatewayResponse, NaturalLanguageResponsePayloadAPI # Assuming these exist for response structuring
from app.modules.sales.services import OrderService, get_order_service
from app.modules.sales.repository import OrderRepository, get_order_repository, ProductRepository, get_product_repository
from app.modules.people.repository import UserRepository, get_user_repository
from app.core.counters import CounterService, get_counter_service
from app.modules.sales.reservation_service import StockReservationService, get_reservation_service
from app.modules.office.services_audit import AuditService, get_audit_service
from app.models.sales import OrderCreateAPI, OrderItemCreateAPI, OrderAPI # API models

# --- Define action function ---

async def create_order_action(payload: dict, user: UserInDB) -> Dict[str, Any]:
    """
    Action function called by the dispatcher for the 'create_order' intent.
    Parses LLM entities, validates them, and calls the OrderService.
    """
    log = logger.bind(intent="create_order", user_id=str(user.id))
    log.info("Executing create_order action...")
    log.debug(f"Received payload (entities): {payload}")

    # 1. Extract and Validate Entities from LLM payload
    raw_items = payload.get("items")
    channel = payload.get("channel", "advisor") # Default channel if not specified
    shipping_address = payload.get("shipping_address") # Optional

    if not raw_items or not isinstance(raw_items, list):
        raise ValueError("Missing or invalid 'items' data for order creation.")

    order_items_api: List[OrderItemCreateAPI] = []
    product_repo: ProductRepository = await get_product_repository()

    # Need to resolve product identifiers (names/SKUs) to ObjectIds
    for item_entity in raw_items:
        identifier = item_entity.get("product_identifier")
        quantity = item_entity.get("quantity")

        if not identifier or not quantity or not isinstance(quantity, int) or quantity <= 0:
            log.warning(f"Skipping invalid item entity: {item_entity}")
            continue # Or raise ValueError? Skip for now to be more robust to LLM errors

        # Find product by identifier (name or SKU) - needs implementation in ProductService/Repo
        product_db = await product_repo.find_product_by_identifier(identifier) # Assumes repo method exists
        if not product_db:
            # Could try fuzzy matching or ask for clarification, but for now raise error
            raise ValueError(f"Product '{identifier}' not found in catalog.")
        if not product_db.is_active:
             raise ValueError(f"Product '{identifier}' is currently unavailable.")

        order_items_api.append(OrderItemCreateAPI(product_id=str(product_db.id), quantity=quantity))

    if not order_items_api:
        raise ValueError("No valid items found to create the order.")

    # Construct the OrderCreateAPI payload
    order_payload_api = OrderCreateAPI(
        items=order_items_api,
        channel=channel,
        shipping_address=shipping_address,
        # billing_address - can LLM extract this?
        # customer_profile_type - can LLM infer this or should we use default?
    )

    # 2. Get Dependencies and Call OrderService
    order_service: OrderService = await get_order_service()
    order_repo: OrderRepository = await get_order_repository()
    user_repo: UserRepository = await get_user_repository()
    counter_service: CounterService = await get_counter_service()
    reservation_service: StockReservationService = await get_reservation_service()
    audit_service: AuditService = await get_audit_service() # Assuming audit is needed

    try:
        # Service expects creator (UserInDB), payload (OrderCreateAPI) and dependencies
        created_order_db = await order_service.create_order(
            order_in=order_payload_api,
            creator=user,
            order_repo=order_repo,
            product_repo=product_repo,
            user_repo=user_repo,
            counter_service=counter_service,
            reservation_service=reservation_service,
            audit_service=audit_service,
        )

        # 3. Format Success Response Data
        # Enrich with customer details before returning
        order_api = await order_service.get_order(str(created_order_db.id), order_repo, user_repo)
        if not order_api: # Should not happen
             log.error("Failed to retrieve created order for response after successful creation.")
             return {"status": "success", "message": f"Order {created_order_db.order_ref} created, but failed to fetch details."}

        # Return the OrderAPI model's dictionary representation
        return order_api.model_dump(mode='json') # Use mode='json' for proper serialization

    except HTTPException as http_exc:
        # Catch exceptions from the service (e.g., stock reservation failure, validation)
        log.warning(f"Order creation failed via service: {http_exc.detail}")
        # Re-raise or convert to a ValueError for the dispatcher to handle?
        # Convert to ValueError for consistency within dispatcher error handling
        raise ValueError(f"Failed to create order: {http_exc.detail}")
    except Exception as e:
        log.exception("Unexpected error during create_order_action")
        raise # Let the main dispatcher handler catch and return internal error


# --- Update INTENT_ACTION_MAP ---

INTENT_ACTION_MAP: Dict[str, Callable[[Dict[str, Any], UserInDB], Awaitable[Any]]] = {
    # ... (other existing intents like get_my_schedule, get_customer_balance, etc.) ...
    "create_order": create_order_action,
    "register_sale": create_order_action, # Alias if needed
    # ...
}

# Make sure the main dispatch_intent function can handle the return value (dict)
# and potentially format it further if needed for the final GatewayResponse.
# The current dispatch_intent seems okay, it expects a dict from the action function.
# Need to ensure ProductRepository has find_product_by_identifier method.

# Add necessary imports at the top if missing
from typing import Dict, Any, Optional, Callable, Awaitable, List
from app.modules.people.models import UserInDB
from bson import ObjectId
# ... other necessary model/service imports ...