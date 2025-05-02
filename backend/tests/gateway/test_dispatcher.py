# tests/gateway/test_dispatcher.py
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.asyncio

@patch("app.modules.gateway.dispatcher.some_service_function", MagicMock(return_value="mocked_response"))
async def test_dispatch_intent():
    """Test dispatching an intent."""
    from app.modules.gateway.dispatcher import dispatch_intent
    response = await dispatch_intent("test_intent", {}, "dummy_user")
    assert response == "mocked_response"