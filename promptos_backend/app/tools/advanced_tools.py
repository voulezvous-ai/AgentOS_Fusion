from loguru import logger
from app.services.mcp_service import mcp_client
from typing import Dict, Any, Optional

async def multi_tool_pipeline(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Pipeline que executa múltiplas ferramentas em sequência.
    """
    log = logger.bind(tool="multi_tool_pipeline")
    if context is None:
        context = {}

    try:
        log.info("Executando pipeline de ferramentas.")
        # Exemplo: Chamar ferramenta 1
        tool1_result = await mcp_client.execute_tool("get_current_weather", {"location": "London", "unit": "metric"})
        if not tool1_result.get("success"):
            log.error("Erro ao executar ferramenta 1.")
            return {"success": False, "message": "Erro na pipeline na ferramenta 1."}

        # Exemplo: Chamar ferramenta 2 com base no resultado da ferramenta 1
        tool2_input = {"amount": 100, "currency": "USD", "user_id": "test_user", "source_token": "mock_token"}
        tool2_result = await mcp_client.execute_tool("process_stripe_payment", tool2_input)
        if not tool2_result.get("success"):
            log.error("Erro ao executar ferramenta 2.")
            return {"success": False, "message": "Erro na pipeline na ferramenta 2."}

        log.success("Pipeline concluída com sucesso.")
        return {"success": True, "message": "Pipeline executada.", "details": {"tool1": tool1_result, "tool2": tool2_result}}
    except Exception as e:
        log.exception("Erro inesperado na pipeline.")
        return {"success": False, "message": f"Erro inesperado: {e}"}