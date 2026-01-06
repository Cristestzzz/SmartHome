# 🏠 SmartHome - Casa Domótica Completa

Sistema IoT completo con ESP32, control web, historial y **5 LEDs controlables**.

---

## ✨ CARACTERÍSTICAS

### 🎮 Control Total:
- ✅ Modo Automático/Manual switchable
- ✅ Ventilador controlado por temperatura
- ✅ Bomba controlada por humedad del suelo
- ✅ Servomotor 0-180°
- ✅ **5 LEDs individuales** (Sala, Cocina, Cuarto, Baño, Pasillo)

### 📊 Monitoreo:
- ✅ Temperatura y humedad ambiental (DHT11)
- ✅ Humedad del suelo (sensor analógico)
- ✅ Dashboard en tiempo real
- ✅ Gráficas interactivas

### ⚙️ Configuración Dinámica:
- ✅ Umbrales de temperatura actualizables
- ✅ Umbrales de humedad de suelo actualizables
- ✅ Cambios aplicados en ~5 segundos

### 📈 Historial:
- ✅ Todos los registros guardados en SQLite
- ✅ Filtros por fecha y cantidad
- ✅ Exportación a CSV

---

## 🔌 CONEXIONES HARDWARE

### ESP32 EMISOR:
```
DHT11:                VCC → 3.3V, DATA → GPIO4, GND → GND
Sensor Suelo:         VCC → 3.3V, AO → GPIO35, GND → GND
```

### ESP32 RECEPTOR:
```
Ventilador (Relé):    IN → GPIO27
Bomba (Relé):         IN → GPIO26
LED Sala:             GPIO13 → 220Ω → LED+ → GND
LED Cocina:           GPIO12 → 220Ω → LED+ → GND
LED Cuarto:           GPIO14 → 220Ω → LED+ → GND
LED Baño:             GPIO25 → 220Ω → LED+ → GND
LED Pasillo:          GPIO33 → 220Ω → LED+ → GND
```

---

## 🚀 INSTALACIÓN RÁPIDA

1. **Instalar ArduinoJson v7** en Arduino IDE
2. **Configurar WiFi e IP** en ESP32 RECEPTOR
3. **Subir códigos** a ambos ESP32
4. **Iniciar servidor**: `pip install -r requirements.txt && python app.py`
5. **Abrir**: http://localhost:5000

---

## 🎮 CONTROL DE LEDs

```
http://localhost:5000/control
→ Cambiar a modo "Manual"
→ Toggle 🏠 LED Sala ON/OFF
→ Toggle 🍳 LED Cocina ON/OFF
→ Toggle 🛏️ LED Cuarto ON/OFF
→ Toggle 🚿 LED Baño ON/OFF
→ Toggle 🚪 LED Pasillo ON/OFF

ESP32 aplica en ~5 segundos
```

---

**¡Sistema Completo!** 🎉💡
