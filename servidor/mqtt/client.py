"""
Cliente MQTT para comunicación con ESP32
"""

import paho.mqtt.client as mqtt
import json
import asyncio
from datetime import datetime
from mqtt.topics import MQTTTopics
from config import MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_CLIENT_ID

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # Almacenar últimos valores de sensores
        self.sensor_data = {
            "temperatura": None,
            "humedad": None,
            "humedad_suelo": None,
            "timestamp": None
        }

        # Callback para broadcast a WebSocket (se asigna desde main.py)
        self.websocket_broadcast = None
        self.db_manager = None
        self.event_loop = None  # Event loop de FastAPI
        
    def connect(self):
        """Conectar al broker MQTT"""
        try:
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            print(f"✓ Conectando a MQTT broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        except Exception as e:
            print(f"✗ Error conectando a MQTT: {e}")
            
    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            print("✓ MQTT conectado exitosamente")
            # Suscribirse a todos los topics de sensores
            self.client.subscribe(MQTTTopics.SENSORES_ALL)
            print(f"✓ Suscrito a: {MQTTTopics.SENSORES_ALL}")
        else:
            print(f"✗ Error de conexión MQTT, código: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta"""
        if rc != 0:
            print(f"⚠️ Desconexión inesperada de MQTT. Reconectando...")
            
    def on_message(self, client, userdata, msg):
        """Callback cuando llega un mensaje MQTT"""
        topic = msg.topic
        payload = msg.payload.decode()
        
        print(f"📨 MQTT: {topic} = {payload}")
        
        # Procesar según el topic
        try:
            if topic == MQTTTopics.TEMPERATURA:
                self.handle_temperatura(float(payload))
            elif topic == MQTTTopics.HUMEDAD:
                self.handle_humedad(float(payload))
            elif topic == MQTTTopics.HUMEDAD_SUELO:
                self.handle_humedad_suelo(int(payload))
        except ValueError as e:
            print(f"✗ Error procesando payload: {e}")
            
    def handle_temperatura(self, value):
        """Procesar temperatura"""
        self.sensor_data["temperatura"] = value
        self.sensor_data["timestamp"] = datetime.now().isoformat()
        self._broadcast_sensor_update("temperatura", value)
        
    def handle_humedad(self, value):
        """Procesar humedad ambiental"""
        self.sensor_data["humedad"] = value
        self.sensor_data["timestamp"] = datetime.now().isoformat()
        self._broadcast_sensor_update("humedad", value)
        
    def handle_humedad_suelo(self, value):
        """Procesar humedad del suelo"""
        self.sensor_data["humedad_suelo"] = value
        self.sensor_data["timestamp"] = datetime.now().isoformat()
        self._broadcast_sensor_update("humedad_suelo", value)
        
        # Si tenemos todos los datos, guardar en BD
        if all(v is not None for v in [
            self.sensor_data["temperatura"],
            self.sensor_data["humedad"],
            self.sensor_data["humedad_suelo"]
        ]):
            self._save_to_database()
            
    def _broadcast_sensor_update(self, sensor_type, value):
        """Enviar actualización por WebSocket"""
        if self.websocket_broadcast and self.event_loop:
            data = {
                "type": "sensor_update",
                "sensor": sensor_type,
                "value": value,
                "timestamp": self.sensor_data["timestamp"]
            }
            # Ejecutar coroutine desde thread externo usando el event loop de FastAPI
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket_broadcast(data),
                    self.event_loop
                )
                print(f"✓ Broadcast enviado: {sensor_type} = {value}")
            except Exception as e:
                print(f"✗ Error en broadcast: {e}")
                
    def _save_to_database(self):
        """Guardar datos completos en base de datos"""
        if self.db_manager:
            try:
                self.db_manager.insertar_lectura_sensores(
                    temperatura=self.sensor_data["temperatura"],
                    humedad=self.sensor_data["humedad"],
                    movimiento=0,
                    distancia=None,
                    humedad_suelo=self.sensor_data["humedad_suelo"]
                )
                print("✓ Datos guardados en BD")
            except Exception as e:
                print(f"✗ Error guardando en BD: {e}")
                
    def publish(self, topic, payload):
        """Publicar mensaje MQTT"""
        try:
            result = self.client.publish(topic, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 MQTT publicado: {topic} = {payload}")
            else:
                print(f"✗ Error publicando MQTT: {result.rc}")
        except Exception as e:
            print(f"✗ Error en publish: {e}")
            
    def publish_actuator_command(self, device, value):
        """Publicar comando a actuador"""
        topic_map = {
            "ventilador": MQTTTopics.VENTILADOR,
            "bomba": MQTTTopics.BOMBA,
            "servo": MQTTTopics.SERVO,
            "led_cuarto1": MQTTTopics.LED_CUARTO1,
            "led_cuarto2": MQTTTopics.LED_CUARTO2,
            "led_cuarto3": MQTTTopics.LED_CUARTO3,
        }
        
        topic = topic_map.get(device)
        if topic:
            # Convertir valor a string apropiado
            if isinstance(value, bool):
                payload = "ON" if value else "OFF"
            else:
                payload = str(value)
            self.publish(topic, payload)
        else:
            print(f"✗ Dispositivo desconocido: {device}")
            
    def loop_start(self):
        """Iniciar loop en thread separado"""
        self.client.loop_start()
        
    def loop_stop(self):
        """Detener loop"""
        self.client.loop_stop()
        
    def disconnect(self):
        """Desconectar del broker"""
        self.client.disconnect()

# Instancia global
mqtt_client = MQTTClient()
