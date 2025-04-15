import time
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

# Importa o setup do logger
from logs.logger import setup_logging
# Importa os roteadores
from routes import profiles, roles, integrations
# Importa as configurações
from schemas.base import Settings

# Carregar configurações
settings = Settings()

# Configurar logging para o microsserviço "agentos-pessoas"
setup_logging(service_name="agentos-pessoas")

app = FastAPI(
    title="AgentOS - Módulo Pessoas",
    description="Serviço para gerenciamento de perfis e roles.",
    version="1.0.0",
)

# --- Middlewares ---

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        with logger.contextualize(trace_id=trace_id):
            start_time = time.time()
            logger.info(f"Requisição recebida: {request.method} {request.url.path}")
            try:
                response = await call_next(request)
                process_time = time.time() - start_time
                response.headers["X-Trace-ID"] = trace_id
                logger.info(f"Requisição finalizada: {request.method} {request.url.path} Status={response.status_code} Tempo={process_time:.4f}s")
                return response
            except Exception as e:
                logger.exception(f"Erro não tratado em: {request.method} {request.url.path}")
                raise e

# Middleware de Autenticação Simples (para teste; substituir por implementação real)
async def auth_middleware(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    user_info = {"id": "guest", "roles": ["guest"]}
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if token == "valid-admin-token":
            user_info = {"id": "admin-user-id", "roles": ["admin", "user", "system"]}
        elif token == "valid-user-token":
            user_info = {"id": "user-id", "roles": ["user", "cliente"]}
        request.state.user = user_info
        logger.info(f"Usuário autenticado: {user_info}")
    else:
        request.state.user = user_info
        logger.info("Requisição sem token de autenticação.")
    response = await call_next(request)
    return response

app.add_middleware(LoggingMiddleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir roteadores
app.include_router(profiles.router, prefix="/v1/profiles", tags=["Profiles"])
app.include_router(roles.router, prefix="/v1/roles", tags=["Roles"])
app.include_router(integrations.router, prefix="/v1/integrations", tags=["Integrações Internas"])

@app.get("/", tags=["Health Check"])
async def root():
    logger.info("Health check acessado.")
    return {"status": "ok", "service": "agentos-pessoas", "version": app.version}

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando o serviço agentos-pessoas...")
    # Conectar ao DB, inicializar caches, etc.
    pass

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Encerrando o serviço agentos-pessoas...")
    # Fechar conexões, limpar recursos.
    pass