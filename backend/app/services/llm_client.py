# agentos_core/app/services/llm_client.py

import httpx  
import json  
from typing import List, Dict, Any, Optional, Union, AsyncGenerator  
from loguru import logger  
from functools import lru_cache  
import asyncio # Para sleep no fallback  
import traceback # Para log detalhado

from app.core.config import settings  
# Importar modelos Pydantic para validação e tipagem  
from app.modules.gateway.models import (  
    LLMResponse, LLMError, LLMResponseMessage,  
    LLMToolCall, LLMResponseChoice, OpenAIMessage  
)  
# Importar tipos Gemini se o fallback for implementado  
# from google.generativeai.types import Content, Part, GenerateContentResponse, GenerationConfig, SafetySetting  
# from google.generativeai import GenerativeModel, configure as configure_google_ai, Types Pydantic

# --- Constantes ---  
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"  
# Adicionar URL do Gemini se/quando implementado  
# GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL or 'gemini-pro'}:generateContent?key={settings.GEMINI_API_KEY}"

# --- Cliente Base (Interface - Opcional, mas boa prática) ---  
class BaseLLMClient(ABC):  
    provider_name: str

    @abstractmethod  
    async def get_completion(  
        self,  
        messages: List[OpenAIMessage],  
        model: str,  
        tools: Optional[List[Dict[str, Any]]] = None,  
        tool_choice: str | Dict = "auto",  
        temperature: float = 0.7,  
        max_tokens: int = 1500,  
        stream: bool = False # Placeholder para futuro  
    ) -> LLMResponse:  
        pass

# --- Cliente OpenAI ---  
class OpenAIClient(BaseLLMClient):  
    provider_name = "OpenAI"

    def __init__(self, api_key: Optional[str] = settings.OPENAI_API_KEY):  
        if not api_key:  
            logger.warning("OpenAI API key not configured. OpenAI features disabled.")  
            self.api_key = None  
            self.headers = None  
            self.aclient = None # Cliente HTTPX  
        else:  
            self.api_key = api_key  
            self.headers = {  
                "Authorization": f"Bearer {self.api_key}",  
                "Content-Type": "application/json",  
                # Opcional: Adicionar Org ID se usar múltiplas organizações  
                # "OpenAI-Organization": settings.OPENAI_ORG_ID  
            }  
            # Criar cliente HTTPX reutilizável  
            self.aclient = httpx.AsyncClient(  
                timeout=60.0, # Timeout geral  
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20), # Limites do pool  
                http2=True # Usar HTTP/2 se suportado  
            )  
            logger.info(f"OpenAI Client initialized for API Key: ...{api_key[-4:]}")

    async def get_completion(  
        self,  
        messages: List[OpenAIMessage],  
        model: str, # Usar modelo passado como argumento  
        tools: Optional[List[Dict[str, Any]]] = None,  
        tool_choice: str | Dict = "auto",  
        temperature: float = 0.7,  
        max_tokens: int = 1500,  
        stream: bool = False # Não implementado ainda  
    ) -> LLMResponse:  
        """Chama a API Chat Completion da OpenAI."""  
        if not self.aclient or not self.headers:  
             logger.error("OpenAI Client not initialized (missing API key).")  
             return LLMResponse(id="error-no-init", object="error", created=0, model=model, choices=[], error=LLMError(message="OpenAI client not initialized."))

        payload = {  
            "model": model,  
            "messages": messages,  
            "temperature": temperature,  
            "max_tokens": max_tokens,  
        }  
        if tools:  
            payload["tools"] = tools  
            payload["tool_choice"] = tool_choice  
        if stream:  
            payload["stream"] = True  
            logger.warning("Streaming requested but not fully implemented in this client version.")

        log = logger.bind(service="LLMClient", provider=self.provider_name, model=model)  
        log.info(f"Sending request to OpenAI Chat Completion (Stream={stream})...")  
        # Logar apenas início do prompt do usuário para evitar PII excessivo  
        if messages: log.debug(f"User Prompt Start: '{messages[-1].get('content', '')[:80]}...'")  
        # log.trace(f"Full Payload (excluding messages): { {k:v for k,v in payload.items() if k != 'messages'} }")

        request_time = datetime.utcnow()  
        try:  
            response = await self.aclient.post(OPENAI_API_URL, headers=self.headers, json=payload)  
            response_time = datetime.utcnow()  
            duration = (response_time - request_time).total_seconds()  
            log.debug(f"OpenAI Response Status: {response.status_code}, Duration: {duration:.3f}s")  
            response.raise_for_status() # Levanta erro para 4xx/5xx

            response_data = response.json()  
            log.trace(f"OpenAI Raw Response Body: {response_data}")

            # Validar e normalizar resposta  
            try:  
                llm_response = LLMResponse.model_validate(response_data)  
                # Tratamento especial para casos onde choices é vazio mas não há erro explícito  
                if not llm_response.choices and not llm_response.error:  
                     # Verificar se há tool_calls na mensagem (OpenAI >v1.x)  
                     first_msg = response_data.get("choices", [{}])[0].get("message", {})  
                     if first_msg.get("tool_calls"):  
                          # É uma chamada de ferramenta, choices pode estar vazio de 'content'  
                          log.debug("Response contains tool_calls, proceeding.")  
                          # Recriar choices dummy se Pydantic removeu? Não, GatewayService lida com isso.  
                     else:  
                          log.warning("OpenAI response OK but missing 'choices' data and no tool_calls.")  
                          # Retornar erro customizado ou resposta vazia? Erro é mais seguro.  
                          llm_response.error = LLMError(message="OpenAI returned no choices or tool calls.")

                log.info(f"OpenAI request successful. Finish Reason: {llm_response.choices[0].finish_reason if llm_response.choices else 'N/A'}")  
                return llm_response

            except Exception as pydantic_error:  
                 log.exception(f"Error validating/processing OpenAI response: {pydantic_error}. Raw data: {response_data}")  
                 return LLMResponse(id="error-validation", object="error", created=int(request_time.timestamp()), model=model, choices=[], error=LLMError(message=f"Failed to parse/validate OpenAI response: {pydantic_error}"))

        except httpx.HTTPStatusError as http_err:  
            error_body_text = http_err.response.text[:500]  
            log.error(f"HTTP Error {http_err.response.status_code} from OpenAI: {error_body_text}")  
            error_details = {"message": f"HTTP error {http_err.response.status_code} from OpenAI"}  
            try: error_details.update(http_err.response.json().get("error", {}))  
            except Exception: pass # Ignorar se corpo do erro não for JSON  
            return LLMResponse(id="error-http", object="error", created=int(request_time.timestamp()), model=model, choices=[], error=LLMError.model_validate(error_details))  
        except httpx.TimeoutException:  
            log.error(f"Timeout error connecting to OpenAI API after {self.aclient.timeout.read}s.")  
            return LLMResponse(id="error-timeout", object="error", created=int(request_time.timestamp()), model=model, choices=[], error=LLMError(message="Request to OpenAI API timed out."))  
        except httpx.RequestError as req_err:  
            log.error(f"Network/Request error calling OpenAI: {req_err}")  
            return LLMResponse(id="error-request", object="error", created=int(request_time.timestamp()), model=model, choices=[], error=LLMError(message=f"Network/Request error calling OpenAI: {req_err}"))  
        except Exception as e:  
             log.exception(f"Unexpected error in OpenAI client during get_completion: {e}")  
             return LLMResponse(id="error-unexpected", object="error", created=int(request_time.timestamp()), model=model, choices=[], error=LLMError(message=f"Unexpected error in OpenAI client: {e}"))

# --- Cliente Gemini (Exemplo - Placeholder/Não Implementado) ---  
class GeminiClient(BaseLLMClient):  
     provider_name = "Gemini"  
     # ... (Implementação similar usando google.generativeai ou httpx) ...  
     async def get_completion(self, ...) -> LLMResponse:  
         logger.error("GeminiClient get_completion not implemented yet.")  
         return LLMResponse(id="error-not-impl", object="error", created=0, model="gemini", choices=[], error=LLMError(message="Gemini client not implemented"))

# --- Função Getter com Cache (Seleciona Cliente) ---  
@lru_cache()  
def get_llm_client_instance(provider: str = "openai") -> BaseLLMClient:  
    """Retorna a instância cacheada do cliente LLM solicitado."""  
    provider_lower = provider.lower()  
    log = logger.bind(service="LLMClientGetter")  
    log.info(f"Solicitando instância do cliente LLM para provider: '{provider_lower}'")

    if provider_lower == "openai":  
        client = OpenAIClient() # Instancia (usa API Key das settings)  
        if not client.api_key:  
             # Levantar erro aqui se OpenAI for essencial e não estiver configurado  
             log.critical("OpenAI Client não pôde ser inicializado (API Key ausente).")  
             raise ValueError("OpenAI API key not configured.")  
        log.debug("Retornando instância cacheada do OpenAIClient.")  
        return client  
    elif provider_lower == "gemini":  
         # Instanciar GeminiClient (requer implementação)  
         # client = GeminiClient()  
         # if not client.is_configured: raise ValueError("Gemini not configured.")  
         # return client  
         log.error("GeminiClient não implementado.")  
         raise ValueError("GeminiClient not implemented.")  
    else:  
        log.error(f"Provider LLM não suportado solicitado: '{provider}'")  
        raise ValueError(f"Unsupported LLM provider: {provider}")

# --- Função Principal com Fallback (Refinada) ---  
async def get_completion_with_fallback(  
     messages: List[OpenAIMessage],  
     model: Optional[str] = None, # Modelo primário  
     # ... outros parâmetros (tools, tool_choice, temp, max_tokens, stream) ...  
     primary_provider: str = "openai",  
     secondary_provider: Optional[str] = "gemini", # Definir fallback padrão ou None  
     use_fallback: bool = True  
) -> LLMResponse:  
     """Tenta o provedor primário, depois o secundário se configurado e habilitado."""  
     log = logger.bind(service="LLMClientFallback")  
     primary_client: Optional[BaseLLMClient] = None  
     result: Optional[LLMResponse] = None

     # Determinar modelo a usar (priorizar override)  
     primary_model = model or (settings.OPENAI_CHAT_MODEL if primary_provider=="openai" else settings.GEMINI_MODEL) # <<< Adicionar modelos default nas settings  
     if not primary_model:  
          log.critical("Modelo LLM primário não definido nas settings ou override!")  
          raise ValueError("Primary LLM model not configured.")

     # 1. Tentar Primário  
     try:  
         primary_client = get_llm_client_instance(primary_provider)  
         log.info(f"Tentando LLM primário: {primary_provider} (Modelo: {primary_model})")  
         result = await primary_client.get_completion(messages=messages, model=primary_model, ...) # Passar outros args  
         # Considerar erro se resposta for vazia ou bloqueada (sem choices/tools E sem erro explícito)  
         is_error_or_empty = result.error or not (result.choices and (result.choices[0].message.content or result.choices[0].message.tool_calls))  
         if is_error_or_empty:  
              log.warning(f"LLM primário '{primary_provider}' falhou ou retornou vazio. Erro: {result.error.message if result.error else 'Empty/Blocked Response'}")  
              if not use_fallback or not secondary_provider:  
                   return result # Retornar o erro/resposta vazia do primário se não houver fallback  
              else:  
                   result = None # Resetar resultado para tentar fallback  
         else:  
             return result # Sucesso no primário

     except (ValueError, HTTPException) as e: # Erro ao obter cliente primário  
         log.error(f"Não foi possível obter cliente LLM primário '{primary_provider}': {e}")  
         if not use_fallback or not secondary_provider: raise # Re-lançar se não houver fallback  
         else: log.warning("Prosseguindo para fallback...")  
     except Exception as e_primary: # Erro durante a chamada API primária  
         log.error(f"Erro na chamada ao LLM primário '{primary_provider}': {e_primary}", exc_info=True)  
         if not use_fallback or not secondary_provider: raise # Re-lançar se não houver fallback  
         else: log.warning("Prosseguindo para fallback...")

     # 2. Tentar Secundário (se result ainda for None)  
     if result is None and use_fallback and secondary_provider:  
         secondary_client: Optional[BaseLLMClient] = None  
         try:  
             secondary_client = get_llm_client_instance(secondary_provider)  
             secondary_model = settings.GEMINI_MODEL or "gemini-1.5-flash-latest" # Modelo fallback  
             log.warning(f"Tentando LLM secundário: {secondary_provider} (Modelo: {secondary_model})")  
             # ADAPTAR CHAMADA SE INTERFACE FOR DIFERENTE (ex: Gemini)  
             # Precisaria de conversão de mensagens e chamada específica  
             if secondary_provider == "gemini":  
                 # result_fallback = await secondary_client.get_completion_gemini(...)  
                 logger.error("Fallback para Gemini não implementado no llm_client.")  
                 raise NotImplementedError("Gemini fallback call not implemented")  
             else: # Assumindo interface OpenAI compatível  
                 result_fallback = await secondary_client.get_completion(messages=messages, model=secondary_model, ...)

             is_fallback_error = result_fallback.error or not (result_fallback.choices and (result_fallback.choices[0].message.content or result_fallback.choices[0].message.tool_calls))  
             if is_fallback_error:  
                 log.error(f"LLM secundário '{secondary_provider}' também falhou ou retornou vazio. Erro: {result_fallback.error.message if result_fallback.error else 'Empty/Blocked Response'}")  
                 # Retornar o erro do secundário  
                 return result_fallback  
             else:  
                 log.info("Fallback LLM bem-sucedido.")  
                 return result_fallback

         except (ValueError, HTTPException) as e_sec_get:  
             log.error(f"Não foi possível obter cliente LLM secundário '{secondary_provider}': {e_sec_get}")  
             raise RuntimeError(f"Primary LLM failed and Fallback LLM '{secondary_provider}' is also unavailable.") from e_sec_get  
         except Exception as e_fallback:  
             log.exception(f"Erro na chamada ao LLM secundário '{secondary_provider}': {e_fallback}")  
             raise RuntimeError(f"Both primary and fallback LLMs failed.") from e_fallback

     # Se chegou aqui, algo deu errado (ex: primário falhou, fallback desabilitado/não configurado)  
     # Deveríamos ter retornado ou levantado erro antes. Adicionar fallback final?  
     final_error_msg = "Failed to get response from primary LLM and fallback was not used or also failed."  
     log.error(final_error_msg)  
     return LLMResponse(id="error-no-provider", object="error", created=int(datetime.utcnow().timestamp()), model="N/A", choices=[], error=LLMError(message=final_error_msg))

# Importar ABC e abstractmethod se usar BaseLLMClient  
from abc import ABC, abstractmethod  
# Importar HTTPException se usado no getter  
from fastapi import HTTPException
