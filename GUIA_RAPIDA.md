# 🚀 INSTALACIÓN Y USO - SISTEMA COMPLETO

## ✨ NUEVAS CARACTERÍSTICAS

✅ **Configuración dinámica de umbrales**  
✅ **Control manual/automático en tiempo real**  
✅ **Historial completo con exportación CSV**  
✅ **Dashboard profesional dark mode**  

---

## 🔧 INSTALACIÓN

### 1. Instalar ArduinoJson v7
```
Arduino IDE → Herramientas → Administrar bibliotecas
Buscar: "ArduinoJson"
Instalar: ArduinoJson v7.4.2 (o superior)
```

### 2. Configurar ESP32 EMISOR
```cpp
Archivo: esp32_emisor/esp32_emisor.ino

Línea 28: WIFI_CHANNEL 11  // Canal del RECEPTOR
Línea 30: receiverMAC[] = {0xXX, ...}  // MAC del RECEPTOR
```

### 3. Configurar ESP32 RECEPTOR
```cpp
Archivo: esp32_receptor/esp32_receptor.ino

Línea 20: WIFI_SSID = "TuWiFi"
Línea 21: WIFI_PASSWORD = "password"
Líneas 24-25: IP del servidor (tu PC)
```

### 4. Iniciar Servidor
```bash
cd servidor_python
pip install -r requirements.txt
python app.py
```

### 5. Abrir Dashboard
```
http://localhost:5000
```

---

## 🎮 USAR EL SISTEMA

### CAMBIAR MODO (Automático ↔ Manual)
```
1. Ir a /control
2. Click en "🤖 Automático" o "🎮 Manual"
3. Cambio instantáneo
```

### CONTROL MANUAL
```
1. Cambiar a modo Manual
2. Toggle ventilador ON/OFF
3. Toggle bomba ON/OFF
4. Slider servo 0-180°
5. ESP32 aplica en ~5 segundos
```

### CONFIGURAR UMBRALES ⭐ NUEVO
```
1. Ir a /control
2. Sección "Configuración de Umbrales Automáticos"
3. Modificar valores:
   - Temperatura activación ventilador
   - Temperatura desactivación ventilador
   - Humedad suelo seco (activar bomba)
   - Humedad suelo húmedo (desactivar bomba)
4. Click "💾 Guardar Configuración"
5. ESP32 actualiza en ~5 segundos ✨
```

### VER HISTORIAL
```
1. Ir a /historial
2. Seleccionar período (1h - 1 mes)
3. Click "📥 Exportar CSV" para descargar
```

---

## 📊 VERIFICACIÓN

### Monitor Serie RECEPTOR debe mostrar:
```
✓ WiFi conectado
IP: 192.168.0.XXX
⚠️  CANAL WiFi: 11

📊 Temp: 28.5°C | Hum: 65.0% | Suelo: 45% | Modo: automatico

[Al cambiar configuración en web]
⚙️  CONFIGURACIÓN ACTUALIZADA:
   Temp ON: 26.5°C | Temp OFF: 33.0°C
   Suelo SECO: 80% | Suelo HÚMEDO: 80%

[Al cambiar a manual en web]
🔄 Modo cambiado a: manual

[Al activar ventilador en web]
🌀 MOTOR ENCENDIDO
```

---

## 🎯 FLUJO COMPLETO

### 1. Configuración Dinámica:
```
Web → Servidor → ESP32 (cada 5s) → Aplica nuevos umbrales
```

### 2. Control Manual:
```
Web → Servidor → ESP32 (cada 5s) → Activa/Desactiva actuadores
```

### 3. Modo Automático:
```
Sensores → Umbrales configurados → Control automático
```

---

## 📝 ENDPOINTS API

- `GET/POST /api/sistema/modo` - Modo automático/manual
- `GET /api/comandos` - Comandos + Configuración ⭐
- `POST /api/control/ventilador` - Control ventilador
- `POST /api/control/bomba` - Control bomba
- `GET/POST /api/configuracion` - Umbrales ⭐
- `GET /api/exportar/csv` - Exportar historial

---

## 🆘 TROUBLESHOOTING

**Configuración no se aplica:**
→ Espera 5 segundos (polling)
→ Verifica Monitor Serie del RECEPTOR
→ Debe mostrar "⚙️ CONFIGURACIÓN ACTUALIZADA"

**Control manual no funciona:**
→ Verifica WiFi del RECEPTOR
→ Espera hasta 5 segundos
→ Revisa Monitor Serie

**Sin datos en historial:**
→ Espera 1 minuto con sistema funcionando
→ Verifica que EMISOR envíe datos
→ Verifica que RECEPTOR envíe al servidor

---

¡Sistema 100% funcional! 🎉
