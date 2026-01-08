"""
API Routes - REST endpoints
"""

from fastapi import APIRouter, HTTPException
from models.schemas import (
    SensorData, ActuadorData, ControlCommand, 
    SystemMode, ThresholdConfig, DataPacket
)
from database.db_manager import DatabaseManager
from mqtt.client import mqtt_client
from mqtt.topics import MQTTTopics
import json

router = APIRouter()
db = DatabaseManager()

# Estado del sistema (migrado de Flask)
sistema_estado = {
    "modo": "automatico",
    "configuracion": {
        "temp_activacion": 30.0,
        "temp_desactivacion": 28.0,
        "humedad_suelo_seco": 30,
        "humedad_suelo_humedo": 70
    }
}

# ==================== DATOS ====================

@router.post("/datos")
async def recibir_datos(data: DataPacket):
    """
    Recibir datos del ESP32 (compatibilidad con código actual)
    """
    try:
        # Guardar sensores en BD
        db.insertar_lectura_sensores(
            temperatura=data.sensores.temperatura,
            humedad=data.sensores.humedad,
            movimiento=data.sensores.movimiento or 0,
            distancia=data.sensores.distancia,
            humedad_suelo=data.sensores.humedad_suelo
        )
        
        # Guardar actuadores en BD
        db.insertar_estado_actuadores(
            servo_angulo=data.actuadores.servo_angulo,
            ventilador_velocidad=data.actuadores.ventilador_velocidad,
            bomba_activa=data.actuadores.bomba_activa,
            leds=json.dumps(data.actuadores.leds)
        )
        
        return {"status": "success", "mensaje": "Datos guardados"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ultimo-estado")
async def ultimo_estado():
    """
    Obtener último estado de sensores y actuadores
    """
    try:
        sensores = db.obtener_ultimas_lecturas(1)
        actuadores = db.obtener_ultimo_estado_actuadores()
        
        if sensores and len(sensores) > 0:
            ultimo_sensor = sensores[0]
            return {
                "sensores": {
                    "temperatura": ultimo_sensor[1],
                    "humedad": ultimo_sensor[2],
                    "movimiento": ultimo_sensor[3],
                    "distancia": ultimo_sensor[4],
                    "humedad_suelo": ultimo_sensor[5],
                    "timestamp": str(ultimo_sensor[6])
                },
                "actuadores": actuadores if actuadores else {}
            }
        else:
            raise HTTPException(status_code=404, detail="No hay datos disponibles")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historial")
async def obtener_historial(limite: int = 100, horas: int = None):
    """
    Obtener historial de lecturas
    """
    try:
        if horas:
            lecturas = db.obtener_lecturas_por_tiempo(horas)
        else:
            lecturas = db.obtener_ultimas_lecturas(limite)
        
        historial = []
        for lectura in lecturas:
            historial.append({
                "id": lectura[0],
                "temperatura": lectura[1],
                "humedad": lectura[2],
                "movimiento": lectura[3],
                "distancia": lectura[4],
                "humedad_suelo": lectura[5],
                "timestamp": str(lectura[6])
            })
        
        return historial
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CONTROL ====================

@router.post("/control/ventilador")
async def controlar_ventilador(command: dict):
    """Control manual del ventilador"""
    if sistema_estado['modo'] != 'manual':
        raise HTTPException(status_code=400, detail="Sistema en modo automático")
    
    estado = command.get('estado', False)
    mqtt_client.publish_actuator_command("ventilador", estado)
    
    # Persistir en BD
    actualizar_estado_actuador_inmediato(ventilador_velocidad=100 if estado else 0)
    
    return {"status": "success", "ventilador": estado}

@router.post("/control/bomba")
async def controlar_bomba(command: dict):
    """Control manual de la bomba"""
    if sistema_estado['modo'] != 'manual':
        raise HTTPException(status_code=400, detail="Sistema en modo automático")
    
    estado = command.get('estado', False)
    mqtt_client.publish_actuator_command("bomba", estado)
    
    # Persistir en BD
    actualizar_estado_actuador_inmediato(bomba_activa=estado)
    
    return {"status": "success", "bomba": estado}

@router.post("/control/servo")
async def controlar_servo(command: dict):
    """Control manual del servomotor"""
    if sistema_estado['modo'] != 'manual':
        raise HTTPException(status_code=400, detail="Sistema en modo automático")
    
    angulo = command.get('angulo', 90)
    if not (0 <= angulo <= 180):
        raise HTTPException(status_code=400, detail="Ángulo debe estar entre 0 y 180")
    
    mqtt_client.publish_actuator_command("servo", angulo)
    
    # Persistir en BD
    actualizar_estado_actuador_inmediato(servo_angulo=angulo)
    
    return {"status": "success", "servo": angulo}

@router.post("/control/led")
async def controlar_led(command: dict):
    """Control manual de LEDs"""
    nombre = command.get('nombre')
    estado = command.get('estado', False)
    
    if not nombre:
        raise HTTPException(status_code=400, detail="Debe especificar el nombre del LED")
    
    # Mapear nombre a dispositivo MQTT
    device_map = {
        "cuarto1": "led_cuarto1",
        "cuarto2": "led_cuarto2",
        "cuarto3": "led_cuarto3"
    }
    
    device = device_map.get(nombre)
    if device:
        mqtt_client.publish_actuator_command(device, estado)
        
        # Persistir en BD
        ultimo = db.obtener_ultimo_estado_actuadores() or {}
        leds_actuales = ultimo.get('leds', {})
        if isinstance(leds_actuales, str):
            leds_actuales = json.loads(leds_actuales)
        leds_actuales[nombre] = estado
        actualizar_estado_actuador_inmediato(leds=leds_actuales)
        
        return {"status": "success", "led": nombre, "estado": estado}
    else:
        raise HTTPException(status_code=400, detail="LED desconocido")

# ==================== SISTEMA ====================

@router.get("/sistema/modo")
async def obtener_modo():
    """Obtener modo actual del sistema"""
    return {"modo": sistema_estado['modo']}

@router.post("/sistema/modo")
async def cambiar_modo(mode: SystemMode):
    """Cambiar modo del sistema"""
    sistema_estado['modo'] = mode.modo
    
    # Publicar por MQTT
    mqtt_client.publish(MQTTTopics.MODO, mode.modo)
    
    return {"status": "success", "modo": mode.modo}

@router.get("/configuracion")
async def obtener_configuracion():
    """Obtener configuración de umbrales"""
    return sistema_estado['configuracion']

@router.post("/configuracion")
async def actualizar_configuracion(config: ThresholdConfig):
    """Actualizar configuración de umbrales"""
    sistema_estado['configuracion'] = config.dict()
    
    # Publicar por MQTT
    mqtt_client.publish(MQTTTopics.CONFIG, json.dumps(config.dict()))
    
    return {"status": "success", "configuracion": sistema_estado['configuracion']}

# ==================== HELPER FUNCTIONS ====================

def actualizar_estado_actuador_inmediato(**kwargs):
    """Actualizar estado de actuadores en BD inmediatamente"""
    try:
        ultimo = db.obtener_ultimo_estado_actuadores() or {}
        
        servo_angulo = kwargs.get('servo_angulo', ultimo.get('servo_angulo', 90))
        ventilador_velocidad = kwargs.get('ventilador_velocidad', ultimo.get('ventilador_velocidad', 0))
        bomba_activa = kwargs.get('bomba_activa', ultimo.get('bomba_activa', False))
        leds = kwargs.get('leds', ultimo.get('leds', {}))
        
        if isinstance(leds, str):
            leds = json.loads(leds)
        
        db.insertar_estado_actuadores(
            servo_angulo=servo_angulo,
            ventilador_velocidad=ventilador_velocidad,
            bomba_activa=bomba_activa,
            leds=json.dumps(leds)
        )
        
        print(f"✓ Estado persistido en BD")
    except Exception as e:
        print(f"✗ Error al persistir estado: {e}")
