import sys
import logging
from loguru import logger
from app.core.config import settings
import uuid
import contextvars

trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("trace_id", default=None)

class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame = logging.currentframe()
        depth = 0
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        if frame is None:
            frame = logging.currentframe()
            depth = 0
        trace_id = trace_id_var.get() or "NONE"
        logger.opt(depth=depth, exception=record.exc_info).bind(trace_id=trace_id).log(level, record.getMessage())

def setup_logging():
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}:{function}:{line}</cyan> | <yellow>TraceID={extra[trace_id]}</yellow> | <level>{message}</level>",
        enqueue=True,
        backtrace=True,
        diagnose=(settings.LOG_LEVEL.upper() == "DEBUG")
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logger.info(f"Logger configurado com nível {settings.LOG_LEVEL.upper()}")