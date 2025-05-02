# tests/modules/delivery/test_delivery_flow.py
import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = pytest.mark.asyncio

async def test_create_delivery(authenticated_client: AsyncClient, db_client):
    """Test creating a delivery."""
    order_id = "dummy_order_id"
    response = await authenticated_client.post(f"/api/v1/deliveries/{order_id}/create")
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["status"] == "pending"
    assert "tracking_history" in response_data