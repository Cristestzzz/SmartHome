# SmartHome MQTT Topics Structure

## Sensores (ESP32 → Servidor)
casa/sensores/temperatura      # float (°C)
casa/sensores/humedad           # float (%)
casa/sensores/humedad_suelo     # int (0-100%)

## Actuadores (Servidor → ESP32)
casa/actuadores/ventilador      # "ON" | "OFF"
casa/actuadores/bomba           # "ON" | "OFF"
casa/actuadores/servo           # int (0-180)
casa/actuadores/leds/cuarto1    # "ON" | "OFF"
casa/actuadores/leds/cuarto2    # "ON" | "OFF"
casa/actuadores/leds/cuarto3    # "ON" | "OFF"

## Sistema (Servidor → ESP32)
casa/sistema/modo               # "automatico" | "manual"
casa/sistema/config             # JSON con umbrales
