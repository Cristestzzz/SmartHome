"""
Pydantic models para validación de datos
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class SensorData(BaseModel):
    """Datos de sensores del ESP32"""
    temperatura: float = Field(..., description="Temperatura en °C")
    humedad: float = Field(..., description="Humedad ambiental en %")
    humedad_suelo: int = Field(..., ge=0, le=100, description="Humedad del suelo 0-100%")
    movimiento: Optional[int] = Field(0, description="Detección de movimiento")
    distancia: Optional[float] = Field(None, description="Distancia en cm")
    timestamp: Optional[str] = None

class ActuadorData(BaseModel):
    """Estado de actuadores"""
    servo_angulo: int = Field(90, ge=0, le=180, description="Ángulo del servo 0-180°")
    ventilador_velocidad: int = Field(0, ge=0, le=100, description="Velocidad ventilador 0-100")
    bomba_activa: bool = Field(False, description="Estado de la bomba")
    leds: Dict[str, bool] = Field(default_factory=dict, description="Estado de LEDs")

class ControlCommand(BaseModel):
    """Comando de control manual"""
    device: str = Field(..., description="Dispositivo: ventilador, bomba, servo, led")
    value: bool | int | str = Field(..., description="Valor del comando")
    led_name: Optional[str] = Field(None, description="Nombre del LED si aplica")

class SystemMode(BaseModel):
    """Modo del sistema"""
    modo: str = Field(..., pattern="^(automatico|manual)$", description="Modo de operación")

class ThresholdConfig(BaseModel):
    """Configuración de umbrales"""
    temp_activacion: float = Field(..., description="Temperatura para activar ventilador")
    temp_desactivacion: float = Field(..., description="Temperatura para desactivar ventilador")
    humedad_suelo_seco: int = Field(..., ge=0, le=100, description="Umbral suelo seco")
    humedad_suelo_humedo: int = Field(..., ge=0, le=100, description="Umbral suelo húmedo")

class DataPacket(BaseModel):
    """Paquete completo de datos (sensores + actuadores)"""
    sensores: SensorData
    actuadores: ActuadorData
