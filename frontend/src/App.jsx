// src/context/WebSocketContext.jsx  
import React, { createContext, useState, useEffect, useCallback, useRef } from 'react';  
import { useAuth } from '../hooks/useAuth'; // Para obter o token ou user ID se necessário

const logger = { info: console.log, error: console.error, warn: console.warn, debug: console.debug };

// Obter URL e API Key do ambiente  
const WS_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws/updates';  
const API_KEY = import.meta.env.VITE_STATIC_API_KEY; // Chave para autenticar WS

const WebSocketContext = createContext(null);

const MAX_RECONNECT_ATTEMPTS = 5;  
const RECONNECT_DELAY_MS = 5000; // 5 segundos

export const WebSocketProvider = ({ children }) => {  
  const [isConnected, setIsConnected] = useState(false);  
  const [lastJsonMessage, setLastJsonMessage] = useState(null);  
  const [error, setError] = useState(null);  
  const webSocketRef = useRef(null);  
  const reconnectAttemptsRef = useRef(0);  
  const reconnectTimeoutRef = useRef(null);

  // Usar o token do AuthContext pode ser útil se a autenticação WS mudar no futuro  
  // const { token, isAuthenticated } = useAuth(); // Descomentar se precisar

  // --- Função de Conexão ---  
  const connectWebSocket = useCallback(() => {  
    // Não conectar se já conectado ou se estiver tentando reconectar  
    if (webSocketRef.current || reconnectTimeoutRef.current) {  
      logger.debug('WebSocket connect call ignored: Already connected or attempting reconnect.');  
      return;  
    }

    // Verificar se a API Key está configurada  
    if (!API_KEY) {  
      logger.error("WebSocket cannot connect: VITE_STATIC_API_KEY is not configured.");  
      setError("Configuração de WebSocket ausente.");  
      setIsConnected(false);  
      return;  
    }

    const urlWithKey = `${WS_URL}?apiKey=${encodeURIComponent(API_KEY)}`;  
    logger.info(`Attempting to connect WebSocket: ${urlWithKey.split('?')[0]}...`); // Não logar a key  
    setError(null); // Limpar erro anterior

    try {  
        const ws = new WebSocket(urlWithKey);  
        webSocketRef.current = ws;

        ws.onopen = () => {  
          logger.success('WebSocket Connected!');  
          setIsConnected(true);  
          setError(null);  
          reconnectAttemptsRef.current = 0; // Resetar tentativas ao conectar  
          // Limpar timeout de reconexão se houver  
          if (reconnectTimeoutRef.current) {  
             clearTimeout(reconnectTimeoutRef.current);  
             reconnectTimeoutRef.current = null;  
          }  
          // Opcional: Enviar mensagem de 'hello' ou 'subscribe' se a API WS exigir  
          // ws.send(JSON.stringify({ type: 'subscribe', channel: 'user_updates' }));  
        };

        ws.onmessage = (event) => {  
          try {  
            const message = JSON.parse(event.data);  
            logger.debug('WebSocket message received:', message);  
            setLastJsonMessage(message); // Atualizar estado com a última mensagem JSON  
          } catch (e) {  
            logger.error('Failed to parse WebSocket message:', event.data, e);  
            // Tratar mensagem não-JSON se necessário  
          }  
        };

        ws.onerror = (event) => {  
          // Erros podem ocorrer antes ou durante a conexão  
          logger.error('WebSocket Error:', event);  
          // A especificação do WS não fornece muitos detalhes no evento 'error'.  
          // O evento 'close' geralmente dá mais informações.  
          setError('Erro na conexão WebSocket.');  
          // onclose será chamado logo após onerror geralmente  
        };

        ws.onclose = (event) => {  
          logger.warn(`WebSocket Disconnected. Code: ${event.code}, Reason: '${event.reason}', Clean: ${event.wasClean}`);  
          setIsConnected(false);  
          webSocketRef.current = null; // Limpar referência

          // Definir erro baseado no código de fechamento  
          if (event.code === 1008 || event.code === 1011) { // Policy violation / Server error  
              setError(`Desconectado: ${event.reason || 'Erro de autenticação/servidor'}`);  
              // Não tentar reconectar em caso de erro de autenticação ou config  
              reconnectAttemptsRef.current = MAX_RECONNECT_ATTEMPTS + 1; // Impedir reconexão  
          } else if (!event.wasClean && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {  
               // Tentativa de Reconexão Automática se não foi fechamento limpo e não excedeu tentativas  
               reconnectAttemptsRef.current += 1;  
               const delay = RECONNECT_DELAY_MS * Math.pow(2, reconnectAttemptsRef.current - 1); // Backoff exponencial  
               setError(`Conexão perdida. Tentando reconectar em ${delay / 1000}s... (Tentativa ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);  
               logger.info(`Attempting reconnect #${reconnectAttemptsRef.current} in ${delay}ms...`);  
               // Agendar reconexão  
               reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay);  
          } else if (!event.wasClean) {  
               setError("Conexão perdida. Máximo de tentativas de reconexão atingido.");  
               logger.error("Max reconnect attempts reached. Giving up.");  
          } else {  
              // Fechamento limpo (ex: logout, server shutdown normal)  
              setError(null); // Limpar erro em caso de desconexão limpa  
          }  
        };

    } catch (err) {  
        logger.error("Failed to create WebSocket instance:", err);  
        setError("Falha ao iniciar conexão WebSocket.");  
        webSocketRef.current = null;  
    }

  }, []); // Sem dependências, pois lê config do env e não depende de auth token diretamente

  // --- Função de Desconexão Manual ---  
  const disconnectWebSocket = useCallback(() => {  
    if (reconnectTimeoutRef.current) {  
        clearTimeout(reconnectTimeoutRef.current);  
        reconnectTimeoutRef.current = null;  
        logger.debug("Reconnect timeout cleared.");  
    }  
    if (webSocketRef.current) {  
      logger.info("Manually disconnecting WebSocket...");  
      // Definir um flag ou remover listeners antes de fechar? Geralmente não necessário.  
      webSocketRef.current.close(1000, "User initiated disconnect"); // Código 1000 = Normal closure  
      // O handler onclose cuidará de limpar state e ref  
    } else {  
        logger.debug("Manual disconnect called but WebSocket already closed.");  
    }  
  }, []);

  // --- Efeito para Conectar/Desconectar ---  
  // Conectar quando o componente montar (e talvez quando autenticar, se WS depender de token)  
  // Desconectar quando desmontar  
  useEffect(() => {  
    // Conectar automaticamente ao montar se tiver API Key  
    // Se precisar esperar autenticação: if (isAuthenticated && API_KEY) { connectWebSocket(); }  
    if (API_KEY) {  
        connectWebSocket();  
    } else {  
        logger.error("Cannot connect WebSocket on mount: API Key missing.");  
        setError("Configuração de WebSocket ausente.");  
    }

    // Cleanup: Desconectar ao desmontar o provider  
    return () => {  
      disconnectWebSocket();  
    };  
  }, [connectWebSocket, disconnectWebSocket]); // Adicionar isAuthenticated se a conexão depender dele

  // --- Função para Enviar Mensagem (se necessário) ---  
  const sendMessage = useCallback((messageObject) => {  
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {  
      try {  
        const messageString = JSON.stringify(messageObject);  
        webSocketRef.current.send(messageString);  
        logger.debug("WebSocket message sent:", messageObject);  
        return true;  
      } catch (e) {  
        logger.error("Failed to stringify/send WebSocket message:", messageObject, e);  
        setError("Falha ao enviar mensagem WebSocket.");  
        return false;  
      }  
    } else {  
      logger.warn("Cannot send message: WebSocket is not connected or open.");  
      setError("Não conectado ao WebSocket para enviar mensagem.");  
      return false;  
    }  
  }, []);

  // Valor fornecido pelo Contexto  
  const contextValue = {  
    isConnected,  
    lastJsonMessage,  
    error,  
    sendMessage, // Expor função de envio se UI precisar mandar pings ou comandos WS  
    connectWebSocket, // Expor para reconexão manual se necessário  
    disconnectWebSocket, // Expor para logout ou outras ações  
  };

  return (  
    <WebSocketContext.Provider value={contextValue}>  
      {children}  
    </WebSocketContext.Provider>  
  );  
};

// Exportar o Contexto para ser usado pelo hook  
export default WebSocketContext;

