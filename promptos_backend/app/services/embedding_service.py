import asyncio
from app.core.config import settings
from loguru import logger
from typing import List, Optional
from openai import AsyncOpenAI, OpenAIError

async def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Gera um vetor embedding para o texto fornecido usando o modelo OpenAI.
    """
    logger.info("Gerando embedding para texto fornecido.")
    if not text.strip():
        logger.warning("Texto vazio ou inválido fornecido para embedding.")
        return None

    try:
        aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await aclient.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        embedding = response.data[0].embedding
        logger.success("Embedding gerado com sucesso.")
        return embedding
    except OpenAIError as e:
        logger.error(f"Erro ao gerar embedding: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao gerar embedding: {e}")
        return None