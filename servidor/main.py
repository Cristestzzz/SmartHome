"""
SmartHome API - FastAPI Backend
Servidor para casa domótica con MQTT y WebSocket
"""

from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

from mqtt.client import mqtt_client
from api.routes import router as api_router
from api.websocket import websocket_manager
from database.db_manager import DatabaseManager

app = FastAPI(
    title="SmartHome API",
    description="API para casa domótica con IoT (MQTT + WebSocket)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configurar Jinja2 para usar request.url_for correctamente
templates.env.globals['url_for'] = lambda name, **params: f"/static/{params.get('path', params.get('filename', ''))}"

# Incluir routers API
app.include_router(api_router, prefix="/api")

# Inicializar base de datos
db = DatabaseManager()

# Conectar MQTT client con WebSocket manager
mqtt_client.websocket_broadcast = websocket_manager.broadcast
mqtt_client.db_manager = db

# ==================== RUTAS WEB ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard principal"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/control", response_class=HTMLResponse)
async def control(request: Request):
    """Página de control manual"""
    return templates.TemplateResponse("control.html", {"request": request})

@app.get("/historial", response_class=HTMLResponse)
async def historial(request: Request):
    """Página de historial"""
    return templates.TemplateResponse("historial.html", {"request": request})

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para comunicación en tiempo real"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Recibir comandos del dashboard
            data = await websocket.receive_json()
            
            # Procesar comandos (control de dispositivos)
            if data.get("type") == "control":
                device = data.get("device")
                value = data.get("value")
                
                # Publicar por MQTT
                mqtt_client.publish_actuator_command(device, value)
                
                # Broadcast a otros clientes
                await websocket_manager.broadcast_actuator_change(device, value)
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket)

# ==================== API HEALTH ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "mqtt": "connected" if mqtt_client.client.is_connected() else "disconnected",
        "websocket": f"{len(websocket_manager.active_connections)} clients"
    }

# ==================== EVENTOS ====================

@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar"""
    print("=" * 60)
    print("🏠 SMARTHOME API - FASTAPI + MQTT + WEBSOCKET")
    print("=" * 60)
    
    # Inicializar base de datos
    try:
        db.crear_tablas()
        print("✓ Base de datos inicializada")
    except Exception as e:
        print(f"✗ Error en base de datos: {e}")
    
    # Conectar MQTT
    mqtt_client.connect()
    mqtt_client.loop_start()
    print("✓ FastAPI iniciado")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar recursos al cerrar"""
    print("\nCerrando servicios...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("✓ Servicios cerrados")

# ==================== MAIN ====================

if __name__ == "__main__":
    print("\n📡 Iniciando servidor en http://0.0.0.0:8000")
    print("📚 Documentación: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/ws\n")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

