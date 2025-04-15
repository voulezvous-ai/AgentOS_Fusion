from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from loguru import logger

class ConnectionManager:
    """
    Gerencia conexões WebSocket para transmissão em tempo real.
    """
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Cliente {client_id} conectado via WebSocket.")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            self.active_connections.pop(client_id)
            logger.info(f"Cliente {client_id} desconectado do WebSocket.")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
                logger.info(f"Mensagem enviada ao cliente {client_id}.")
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem para {client_id}: {e}")
        else:
            logger.warning(f"Cliente {client_id} não encontrado para envio de mensagem.")

    async def broadcast(self, message: dict):
        """
        Envia uma mensagem para todos os clientes conectados.
        """
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
                logger.info(f"Mensagem broadcast enviada para cliente {client_id}.")
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem para {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Remove clientes desconectados
        for client_id in disconnected_clients:
            self.disconnect(client_id)
            logger.warning(f"Removendo cliente desconectado: {client_id}.")

# Singleton para gerenciar as conexões
manager = ConnectionManager()