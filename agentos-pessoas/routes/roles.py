from fastapi import APIRouter, Depends, HTTPException, status
from schemas.role import RoleCreate, RoleRead
from schemas.base import MsgDetail
from services.role_service import RoleService
from utils.auth import require_role

router = APIRouter()

def get_role_service():
    return RoleService()

@router.post(
    "/",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova role",
    dependencies=[Depends(require_role(["admin"]))]
)
async def create_role(role_in: RoleCreate, service: RoleService = Depends(get_role_service)):
    new_role = await service.create_role(role_in)
    if not new_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role já existe ou dados inválidos.")
    return new_role

@router.get(
    "/",
    response_model=list[RoleRead],
    summary="Listar todas as roles",
    dependencies=[Depends(require_role(["admin", "vendedor"]))]
)
async def list_roles(service: RoleService = Depends(get_role_service)):
    return await service.get_roles()