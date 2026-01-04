# 🏠 CASA DOMÓTICA - SISTEMA COMPLETO

Sistema de automatización del hogar con **control manual/automático real**, dashboard profesional y historial completo.

---

## ✨ CARACTERÍSTICAS COMPLETAS

### 🎮 Control Bidireccional Real:
- ✅ **Modo Automático**: Sensores controlan actuadores
- ✅ **Modo Manual**: Control total desde la web
- ✅ **Cambio en tiempo real**: Sin necesidad de reiniciar
- ✅ **Comandos reales**: ESP32 consulta servidor cada 5s

### 📊 Dashboard Premium:
- ✅ Sidebar lateral profesional
- ✅ Métricas en tiempo real
- ✅ Gráficas interactivas
- ✅ Indicador de estado

### 📈 Historial Completo:
- ✅ Tabla con todos los registros
- ✅ Filtros por fecha y cantidad
- ✅ Exportación a CSV
- ✅ Estados visuales con badges

### ⚙️ Configuración de Umbrales:
- ✅ Temperatura activación/desactivación ventilador
- ✅ Humedad suelo seco/húmedo para bomba
- ✅ Guardado en servidor
- ✅ Actualización en tiempo real

---

## 🔄 FLUJO DE CONTROL

### MODO AUTOMÁTICO (Default):
```
ESP32 EMISOR → Sensores → ESP32 RECEPTOR
                              ↓
                     ¿Temp >= 30°C? → Ventilador ON
                     ¿Temp <= 28°C? → Ventilador OFF
                     ¿Suelo < 30%?  → Bomba ON
                     ¿Suelo > 70%?  → Bomba OFF
                              ↓
                       Servidor Flask
                              ↓
                       Dashboard Web
```

### MODO MANUAL:
```
Usuario Web → Servidor Flask → ESP32 RECEPTOR
                                      ↓
                              Actuadores (Motor/Bomba)
                                      ↓
                              Dashboard Web (feedback)
```

---

## 🚀 INSTALACIÓN COMPLETA

### PASO 1: Librerías Arduino

**Instalar en Arduino IDE:**
1. Abrir Arduino IDE
2. Ir a **Herramientas** → **Administrar bibliotecas**
3. Buscar e instalar:
   - `DHT sensor library` by Adafruit
   - `ArduinoJson` by Benoit Blanchon (versión 6.x)

### PASO 2: Configurar ESP32 EMISOR

**Archivo:** `esp32_emisor/esp32_emisor.ino`

```cpp
// Línea 28: Canal WiFi
#define WIFI_CHANNEL 11  // ← Tu canal (del RECEPTOR)

// Línea 30: MAC del RECEPTOR
uint8_t receiverMAC[] = {0xEC, 0x64, 0xC9, 0x91, 0xBD, 0x3C};  // ← Cambiar
```

### PASO 3: Configurar ESP32 RECEPTOR

**Archivo:** `esp32_receptor/esp32_receptor.ino`

```cpp
// Línea 20: WiFi
const char* WIFI_SSID = "TuWiFi";        // ← Tu WiFi
const char* WIFI_PASSWORD = "TuPassword";  // ← Tu password

// Línea 23: URLs del servidor
const char* SERVER_URL_DATOS = "http://TU_IP:5000/api/datos/datos";
const char* SERVER_URL_COMANDOS = "http://TU_IP:5000/api/comandos";
```

### PASO 4: Servidor Python

```bash
cd servidor_python
pip install -r requirements.txt
python app.py
```

### PASO 5: Abrir Dashboard

```
http://localhost:5000
```

---

## 🎮 USO DEL SISTEMA

### Cambiar de Modo:

**En la página Control:**
1. Click en **🤖 Automático** o **🎮 Manual**
2. Cambio instantáneo sin reiniciar

### Control Manual:

**Habilita los controles:**
1. Cambiar a modo **Manual**
2. Toggle ventilador ON/OFF
3. Toggle bomba ON/OFF
4. Slider servo 0-180°
5. ESP32 aplicará comandos en 5 segundos

### Configurar Umbrales:

**En la página Control:**
1. Modificar valores de temperatura/humedad
2. Click en **💾 Guardar Configuración**
3. Aplica inmediatamente en modo automático

### Ver Historial:

**En la página Historial:**
1. Seleccionar período (1h - 1 mes)
2. Elegir cantidad de registros
3. Click **📥 Exportar CSV** para descargar

---

## 📡 ENDPOINTS DE LA API

### Datos:
- `POST /api/datos` - Recibir datos del ESP32
- `GET /api/ultimo-estado` - Último estado
- `GET /api/historial?horas=24&limite=100` - Historial filtrado

### Control:
- `GET/POST /api/sistema/modo` - Obtener/cambiar modo
- `GET /api/comandos` - Consultar comandos (ESP32)
- `POST /api/control/ventilador` - Controlar ventilador
- `POST /api/control/bomba` - Controlar bomba
- `POST /api/control/servo` - Controlar servo

### Configuración:
- `GET/POST /api/configuracion` - Umbrales automáticos

### Exportar:
- `GET /api/exportar/csv?horas=24` - Descargar CSV

---

## 🔌 CONEXIONES HARDWARE

### ESP32 EMISOR:
```
DHT11:
  VCC  → 3.3V
  DATA → GPIO4 + Resistor 10kΩ → 3.3V
  GND  → GND

Sensor Humedad Suelo:
  VCC → 3.3V
  AO  → GPIO35
  GND → GND
```

### ESP32 RECEPTOR:
```
Relé Ventilador (GPIO27):
  VCC → 5V
  GND → GND
  IN  → GPIO27

Relé Bomba (GPIO26):
  VCC → 5V
  GND → GND
  IN  → GPIO26

⚠️ TIERRA COMÚN:
  ESP32 GND ← → Fuente Externa GND
```

---

## 📊 CARACTERÍSTICAS TÉCNICAS

### ESP32 RECEPTOR - Polling:
- Consulta comandos cada **5 segundos**
- Envía datos cada **10 segundos**
- Timeout de seguridad: **15 segundos**

### Servidor Flask:
- Estado en memoria (modo, comandos, config)
- Base de datos SQLite para historial
- CORS habilitado para desarrollo

### Frontend:
- Actualización dashboard: **5 segundos**
- Cambio de modo: **Instantáneo**
- Aplicación de comandos: **Hasta 5 segundos** (próximo polling)

---

## 🎯 ESTRUCTURA DEL PROYECTO

```
casa_domotica_completo/
├── README.md
│
├── esp32_emisor/
│   └── esp32_emisor.ino
│
├── esp32_receptor/
│   └── esp32_receptor.ino (⭐ CON POLLING DE COMANDOS)
│
└── servidor_python/
    ├── app.py (⭐ CON API COMPLETA)
    ├── requirements.txt
    ├── database/
    │   └── db_manager.py
    ├── static/
    │   ├── css/
    │   │   └── styles_premium.css
    │   └── js/
    │       └── dashboard_premium.js
    └── templates/
        ├── index.html (Dashboard)
        ├── control.html (⭐ CONTROL MANUAL/AUTO)
        └── historial.html (⭐ HISTORIAL + CSV)
```

---

## 🆘 TROUBLESHOOTING

### "Control manual no funciona":
→ Verifica que ESP32 RECEPTOR tenga WiFi
→ Espera hasta 5 segundos (polling de comandos)
→ Revisa Monitor Serie del RECEPTOR

### "No cambia de modo":
→ Verifica que el servidor Flask esté corriendo
→ Abre consola del navegador (F12) para ver errores
→ Verifica que el ESP32 consulte `/api/comandos`

### "Error al exportar CSV":
→ Verifica que haya datos en la base de datos
→ Espera al menos 1 minuto con el sistema funcionando

### "ESP32 no consulta comandos":
→ Verifica las URLs en el código del RECEPTOR
→ Verifica que ArduinoJson esté instalado
→ Revisa Monitor Serie para ver logs de polling

---

## 📚 DEPENDENCIAS

### Arduino:
```
- DHT sensor library (Adafruit)
- ArduinoJson (v6.x)
- ESP32 Core (v2.x o v3.x)
```

### Python:
```
- Flask==3.0.0
- Flask-CORS==4.0.0
```

---

## 🎓 PARA PROYECTO ACADÉMICO

### Características Destacadas:
1. ✅ **Control bidireccional real** (no simulado)
2. ✅ **Modo automático Y manual** funcionando
3. ✅ **Dashboard profesional** estilo aplicación comercial
4. ✅ **Historial completo** con exportación
5. ✅ **Configuración dinámica** de umbrales
6. ✅ **Arquitectura completa** IoT end-to-end

### Puntos para Presentación:
- Comunicación ESP-NOW sin WiFi en emisor
- Polling inteligente para comandos
- UI/UX profesional con sidebar
- Base de datos con histórico
- Exportación de datos a CSV
- Sistema modular y escalable

---

## 👨‍💻 CRÉDITOS

Proyecto desarrollado para:  
**Universidad Nacional Amazónica de Madre de Dios (UNAMAD)**  
Ingeniería de Sistemas e Informática

---

**¡Sistema Completo Funcionando!** 🎉
