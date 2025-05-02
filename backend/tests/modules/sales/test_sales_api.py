# tests/modules/sales/test_sales_api.py
import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = pytest.mark.asyncio

async def test_create_order_success(authenticated_client: AsyncClient, db_client):
    """Test successful creation of an order."""
    payload = {
        "items": [{"product_id": "dummy_product_id", "quantity": 2}],
        "channel": "test_channel"
    }
    response = await authenticated_client.post("/api/v1/orders/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["status"] == "pending"
    assert response_data["channel"] == "test_channel"