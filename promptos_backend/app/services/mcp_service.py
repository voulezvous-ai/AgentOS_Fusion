
# ... conteúdo original preservado ...
# --- Adicionar Literal e date aos imports ---
from typing import Literal, List, Dict, Any, Optional, Type
from datetime import date

# --- NOVO: Schema para Handoff ---
class HandoffParams(BaseModel):
    target_agent: Literal["SalesAgent", "SupportAgent", "DeliveryAgent", "GeneralAssistant"]
    summary_for_handoff: str = Field(..., description="A concise summary of the conversation and the reason for the handoff.")
    user_query: Optional[str] = Field(None, description="The specific user query that triggered the handoff, if applicable.")

# --- Atualizar MCPRegistry ---
# Substitua o conteúdo _tools por este novo dicionário
_tools: Dict[str, Dict[str, Any]] = {
    "handoff_to_agent": {
        "description": "Transfers the conversation to a specialized agent when the current one cannot handle the request.",
        "params_schema": HandoffParams,
        "response_schema": None,
        "auth_required": None,
        "internal_action": True
    }
    # ... manter outras ferramentas como estão, ou adicionar refinadas se necessário ...
}
