# Guía de Inicio - SmartHome FastAPI + MQTT

## 1. Iniciar Mosquitto (MQTT Broker)

### Windows:
```bash
# Abrir terminal como administrador
mosquitto -v

# O si está instalado como servicio:
net start mosquitto
```

Deberías ver:
```
1736291234: mosquitto version 2.x starting
1736291234: Opening ipv4 listen socket on port 1883.
```

## 2. Iniciar Servidor FastAPI

### Terminal 1: FastAPI
```bash
cd c:\Users\ADMIN\automatas\SmartHome\servidor
python main.py
```

Deberías ver:
```
==============================================================
🏠 SMARTHOME API - FASTAPI + MQTT + WEBSOCKET
==============================================================
✓ Base de datos inicializada
✓ Conectando a MQTT broker: localhost:1883
✓ MQTT conectado exitosamente
✓ Suscrito a: casa/sensores/#
✓ FastAPI iniciado

📡 Iniciando servidor en http://0.0.0.0:8000
📚 Documentación: http://localhost:8000/docs
🔌 WebSocket: ws://localhost:8000/ws
```

## 3. Verificar Funcionamiento

### Abrir en navegador:
- Dashboard: http://localhost:8000
- Swagger API: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

### Health Check debería mostrar:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "mqtt": "connected",
  "websocket": "0 clients"
}
```

## 4. Probar MQTT (Opcional)

### Publicar mensaje de prueba:
```bash
mosquitto_pub -t "casa/sensores/temperatura" -m "25.5"
```

Deberías ver en el servidor FastAPI:
```
📨 MQTT: casa/sensores/temperatura = 25.5
```

## 5. Siguiente Paso

Actualizar el código del ESP32 para usar MQTT en lugar de HTTP.
