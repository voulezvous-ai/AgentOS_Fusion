from typing import List, Optional
from loguru import logger
import uuid
from schemas.role import RoleCreate, RoleRead

# Banco de dados fake para roles
fake_role_db = {
    "role-admin-uuid": {"id": "role-admin-uuid", "name": "admin", "description": "Administrador do sistema"},
    "role-cliente-uuid": {"id": "role-cliente-uuid", "name": "cliente", "description": "Usuário final"},
    "role-vendedor-uuid": {"id": "role-vendedor-uuid", "name": "vendedor", "description": "Agente de vendas"},
}

class RoleService:
    def __init__(self):
        logger.info("RoleService inicializado.")

    async def create_role(self, role_in: RoleCreate) -> Optional[RoleRead]:
        logger.info(f"Criando role: {role_in.name}")
        for r in fake_role_db.values():
            if r["name"] == role_in.name:
                logger.warning("Role já existe.")
                return None
        role_id = f"role-{role_in.name.lower()}-{str(uuid.uuid4())[:4]}"
        new_role = role_in.dict()
        new_role["id"] = role_id
        fake_role_db[role_id] = new_role
        logger.success(f"Role criada: {role_in.name} (ID={role_id})")
        return RoleRead(**new_role)

    async def get_roles(self) -> List[RoleRead]:
        logger.info("Listando roles.")
        return [RoleRead(**r) for r in fake_role_db.values()]