"""
WebSocket manager para comunicación en tiempo real con el dashboard
"""

from fastapi import WebSocket
from typing import List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        """Aceptar nueva conexión WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✓ Cliente WebSocket conectado. Total: {len(self.active_connections)}")
        
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Conectado al servidor SmartHome"
        })
        
    def disconnect(self, websocket: WebSocket):
        """Desconectar cliente WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"✗ Cliente WebSocket desconectado. Total: {len(self.active_connections)}")
            
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Enviar mensaje a un cliente específico"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"✗ Error enviando mensaje personal: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, message: dict):
        """Enviar mensaje a todos los clientes conectados"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"✗ Error en broadcast: {e}")
                disconnected.append(connection)
                
        # Limpiar conexiones muertas
        for conn in disconnected:
            self.disconnect(conn)
            
    async def broadcast_sensor_data(self, sensor_data: dict):
        """Broadcast específico para datos de sensores"""
        await self.broadcast({
            "type": "sensor_data",
            "data": sensor_data
        })
        
    async def broadcast_actuator_change(self, device: str, value):
        """Broadcast específico para cambios en actuadores"""
        await self.broadcast({
            "type": "actuator_change",
            "device": device,
            "value": value
        })

# Instancia global
websocket_manager = WebSocketManager()
