from fastapi import APIRouter, Depends, HTTPException, status, Request
from shared_auth import verify_s2s_token  # Placeholder; implemente em shared_auth
from logs.logger import logger
from schemas.profile import ProfileRead
from schemas.base import MsgDetail
from services.profile_service import ProfileService
import uuid

router = APIRouter(tags=["Integrações Internas"])

def get_profile_service():
    return ProfileService()

async def verify_s2s_or_user_permission(request: Request):
    s2s_token = request.headers.get("X-Service-Token")
    auth_header = request.headers.get("Authorization")
    if s2s_token and verify_s2s_token(s2s_token):
        logger.debug("Validação S2S bem-sucedida.")
        return True
    if auth_header and auth_header.startswith("Bearer "):
        from utils.auth import require_role, get_current_user
        try:
            user_checker = require_role(["system", "admin"])
            await user_checker(await get_current_user(request))
            logger.debug("Validação JWT para acesso interno bem-sucedida.")
            return True
        except Exception as e:
            logger.warning(f"Falha na validação JWT para acesso interno: {e}")
    logger.error("Validação S2S/JWT falhou para acesso interno.")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autorizado para acesso interno.")

@router.get(
    "/profile/{profile_id}",
    response_model=ProfileRead,
    summary="[Interno] Obter dados de perfil por ID",
    dependencies=[Depends(verify_s2s_or_user_permission)],
    responses={404: {"model": MsgDetail, "description": "Perfil não encontrado"}}
)
async def get_profile_for_internal_use(profile_id: str, request: Request, service: ProfileService = Depends(get_profile_service)):
    trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
    logger.info(f"Buscando perfil interno {profile_id}", extra={"trace_id": trace_id})
    pessoa = await service.get_profile_by_id(profile_id, internal_call=True)
    if not pessoa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
    return pessoa