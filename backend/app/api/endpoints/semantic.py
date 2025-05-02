# api/endpoints/semantic.py
import logging
import uuid
from fastapi import APIRouter, HTTPException, status, Depends, Body, Request
from typing import Annotated

from schemas.semantic import ProcessRequestInput, ProcessRequestOutput, LLMResponse
from services.llm_client import BaseLLMClient, get_llm_service
from services.dispatcher import dispatch_intent
from utils.security import Authenticated
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/process_request",
    response_model=ProcessRequestOutput,
    summary="Process Natural Language Command",
    description="Receives a natural language command, interprets it using an LLM, "
                "and dispatches it to the appropriate AgentOS module.",
    tags=["Semantic Gateway"],
    dependencies=[Authenticated],
)
async def process_natural_language_request(
    request_data: Annotated[ProcessRequestInput, Body()],
    llm_client: Annotated[BaseLLMClient, Depends(get_llm_service)],
    request: Request
) -> ProcessRequestOutput:
    request_id = str(uuid.uuid4())
    client_host = request.client.host if request.client else "unknown"
    user_id = request_data.user_id

    logger.info(f"RID={request_id} - Received /process_request from {client_host} (User: {user_id}): '{request_data.text}'")

    llm_response: LLMResponse | None = None
    dispatcher_result: dict | None = None

    try:
        llm_response = await llm_client.get_intent_and_entities(
            text=request_data.text,
            session_id=request_data.session_id
        )
        logger.info(f"RID={request_id} - LLM Result: Intent='{llm_response.intent}', Entities={llm_response.entities}")

        dispatcher_result = await dispatch_intent(
            intent=llm_response.intent,
            entities=llm_response.entities,
            user_id=user_id
        )
        logger.info(f"RID={request_id} - Dispatch successful for intent '{llm_response.intent}'. Result: {dispatcher_result}")

        final_status = dispatcher_result.get("status", "success")
        final_message = dispatcher_result.get("message", f"Action for intent '{llm_response.intent}' completed.")
        final_data = dispatcher_result

    except ValueError as e:
        logger.warning(f"RID={request_id} - Value Error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"RID={request_id} - Unexpected error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

    return ProcessRequestOutput(
        status=final_status,
        message=final_message,
        intent=llm_response.intent,
        data=final_data,
        request_id=request_id
    )