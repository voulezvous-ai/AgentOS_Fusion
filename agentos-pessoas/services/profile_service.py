from typing import List, Optional
from loguru import logger
import uuid
from datetime import datetime, timezone
from schemas.profile import ProfileCreate, ProfileUpdate, ProfileRead, ProfileFilter

# Simulação de banco de dados em memória
fake_profile_db = {}
fake_role_assignment_db = {}

class ProfileService:
    def __init__(self):
        logger.info("ProfileService inicializado.")

    async def create_profile(self, profile_in: ProfileCreate) -> Optional[ProfileRead]:
        logger.info(f"Criando perfil para: {profile_in.email}")
        for profile in fake_profile_db.values():
            if profile["email"] == profile_in.email:
                logger.warning(f"Email {profile_in.email} já existe.")
                return None
        profile_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        new_profile = profile_in.dict()
        new_profile.update({
            "id": profile_id,
            "created_at": now,
            "updated_at": now,
            "roles": []
        })
        fake_profile_db[profile_id] = new_profile
        if profile_in.initial_roles:
            fake_role_assignment_db[profile_id] = list(set(profile_in.initial_roles))
            new_profile["roles"] = fake_role_assignment_db[profile_id]
            logger.info(f"Roles {profile_in.initial_roles} atribuídas ao perfil {profile_id}")
        logger.success(f"Perfil criado: ID={profile_id}")
        return ProfileRead(**new_profile)

    async def get_profiles(self, filters: ProfileFilter, skip: int = 0, limit: int = 100, trace_id: Optional[str] = None) -> List[ProfileRead]:
        logger.info(f"Listando perfis com filtros: {filters.dict(exclude_unset=True)}")
        results = []
        for profile in fake_profile_db.values():
            match = True
            if filters.email and filters.email not in profile.get("email", ""):
                match = False
            if filters.name and filters.name.lower() not in f"{profile.get('first_name','')} {profile.get('last_name','')}".lower():
                match = False
            if filters.profile_type and profile.get("profile_type") != filters.profile_type:
                match = False
            if filters.is_active is not None and profile.get("is_active") != filters.is_active:
                match = False
            if filters.role:
                roles = fake_role_assignment_db.get(profile["id"], [])
                if filters.role not in roles:
                    match = False
            if match:
                profile_data = profile.copy()
                profile_data["roles"] = fake_role_assignment_db.get(profile["id"], [])
                results.append(ProfileRead(**profile_data))
        return results[skip: skip + limit]

    async def get_profile_by_id(self, profile_id: str, internal_call: bool = False) -> Optional[ProfileRead]:
        logger.info(f"Buscando perfil por ID: {profile_id}")
        profile = fake_profile_db.get(profile_id)
        if profile:
            profile_data = profile.copy()
            profile_data["roles"] = fake_role_assignment_db.get(profile_id, [])
            return ProfileRead(**profile_data)
        logger.warning(f"Perfil {profile_id} não encontrado.")
        return None

    async def update_profile(self, profile_id: str, profile_in: ProfileUpdate) -> Optional[ProfileRead]:
        logger.info(f"Atualizando perfil {profile_id}")
        profile = fake_profile_db.get(profile_id)
        if not profile:
            logger.warning(f"Perfil não encontrado: {profile_id}")
            return None
        update_data = profile_in.dict(exclude_unset=True)
        if "email" in update_data and update_data["email"] != profile["email"]:
            for pid, p in fake_profile_db.items():
                if pid != profile_id and p["email"] == update_data["email"]:
                    logger.warning("Email duplicado.")
                    return None
        profile.update(update_data)
        profile["updated_at"] = datetime.now(timezone.utc)
        fake_profile_db[profile_id] = profile
        profile["roles"] = fake_role_assignment_db.get(profile_id, [])
        logger.success(f"Perfil {profile_id} atualizado.")
        return ProfileRead(**profile)

    async def delete_profile(self, profile_id: str) -> bool:
        logger.info(f"Deletando perfil {profile_id}")
        if profile_id in fake_profile_db:
            del fake_profile_db[profile_id]
            if profile_id in fake_role_assignment_db:
                del fake_role_assignment_db[profile_id]
            logger.success(f"Perfil {profile_id} deletado.")
            return True
        logger.warning(f"Perfil {profile_id} não encontrado para deleção.")
        return False