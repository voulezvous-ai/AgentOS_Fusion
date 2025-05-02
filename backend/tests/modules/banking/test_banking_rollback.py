# tests/modules/banking/test_banking_rollback.py
import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = pytest.mark.asyncio

async def test_transaction_rollback(authenticated_client: AsyncClient, db_client):
    """Test transaction rollback."""
    transaction_id = "dummy_transaction_id"
    payload = {"reason": "Test rollback"}
    response = await authenticated_client.post(f"/api/v1/transactions/{transaction_id}/rollback", json=payload)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["status"] == "rolled_back"
    assert response_data["rollback_reason"] == "Test rollback"