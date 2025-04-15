from fastapi import APIRouter, Depends, HTTPException, status, Request
from schemas.profile import ProfileCreate, ProfileUpdate, ProfileRead, ProfileFilter
from schemas.base import MsgDetail
from services.profile_service import ProfileService
from utils.auth import get_current_active_user, require_role

router = APIRouter()

def get_profile_service():
    return ProfileService()

@router.post(
    "/",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo perfil",
    dependencies=[Depends(require_role(["admin"]))]
)
async def create_profile(profile_in: ProfileCreate, service: ProfileService = Depends(get_profile_service)):
    new_profile = await service.create_profile(profile_in)
    if not new_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não foi possível criar o perfil. Verifique os dados.")
    return new_profile

@router.get(
    "/",
    response_model=list[ProfileRead],
    summary="Listar perfis com filtros",
    dependencies=[Depends(require_role(["admin", "vendedor"]))]
)
async def list_profiles(request: Request, filters: ProfileFilter = Depends(), skip: int = 0, limit: int = 100, service: ProfileService = Depends(get_profile_service)):
    profiles = await service.get_profiles(filters=filters, skip=skip, limit=limit, trace_id=request.headers.get("X-Trace-ID"))
    return profiles

@router.get(
    "/{profile_id}",
    response_model=ProfileRead,
    summary="Obter detalhes de um perfil",
    responses={404: {"model": MsgDetail, "description": "Perfil não encontrado"}},
    dependencies=[Depends(require_role(["admin", "vendedor", "cliente"]))]
)
async def get_profile(profile_id: str, service: ProfileService = Depends(get_profile_service), current_user: dict = Depends(get_current_active_user)):
    if "admin" not in current_user["roles"] and "vendedor" not in current_user["roles"]:
        if profile_id != current_user.get("profile_id"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a este perfil")
    profile = await service.get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
    return profile

@router.put(
    "/{profile_id}",
    response_model=ProfileRead,
    summary="Atualizar um perfil",
    responses={404: {"model": MsgDetail, "description": "Perfil não encontrado"}},
    dependencies=[Depends(require_role(["admin"]))]
)
async def update_profile(profile_id: str, profile_in: ProfileUpdate, service: ProfileService = Depends(get_profile_service)):
    updated_profile = await service.update_profile(profile_id, profile_in)
    if not updated_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado para atualização")
    return updated_profile

@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar um perfil",
    responses={404: {"model": MsgDetail, "description": "Perfil não encontrado"}},
    dependencies=[Depends(require_role(["admin"]))]
)
async def delete_profile(profile_id: str, service: ProfileService = Depends(get_profile_service)):
    deleted = await service.delete_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado para deleção")
    return None