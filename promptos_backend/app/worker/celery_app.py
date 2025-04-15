from celery import Celery
from app.core.config import settings
from loguru import logger

# Criação da instância Celery
celery_app = Celery("promptos_backend")

# Configuração do Celery usando as variáveis de ambiente
celery_app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_default_queue="default",
    task_default_retry_delay=60,
    task_ignore_result=True,
    worker_max_tasks_per_child=100,
    worker_hijack_root_logger=False
)

@celery_app.task(bind=True)
def health_check_task(self):
    logger.info("Celery health check task executed successfully.")
    return {"status": "ok"}

logger.info("Celery app configurado com sucesso.")