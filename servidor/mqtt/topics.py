"""
MQTT Topics definitions
"""

class MQTTTopics:
    """Definición centralizada de topics MQTT"""
    
    # Sensores (ESP32 → Servidor)
    TEMPERATURA = "casa/sensores/temperatura"
    HUMEDAD = "casa/sensores/humedad"
    HUMEDAD_SUELO = "casa/sensores/humedad_suelo"
    SENSORES_ALL = "casa/sensores/#"
    
    # Actuadores (Servidor → ESP32)
    VENTILADOR = "casa/actuadores/ventilador"
    BOMBA = "casa/actuadores/bomba"
    SERVO = "casa/actuadores/servo"
    LED_CUARTO1 = "casa/actuadores/leds/cuarto1"
    LED_CUARTO2 = "casa/actuadores/leds/cuarto2"
    LED_CUARTO3 = "casa/actuadores/leds/cuarto3"
    ACTUADORES_ALL = "casa/actuadores/#"
    
    # Sistema (Servidor → ESP32)
    MODO = "casa/sistema/modo"
    CONFIG = "casa/sistema/config"
    SISTEMA_ALL = "casa/sistema/#"
