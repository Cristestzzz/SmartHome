# 🚀 Guía de Instalación - Servidor SmartHome

> **Para la laptop que actuará como servidor**

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener:
- Windows 10/11
- Conexión a internet
- Acceso a la red WiFi donde estarán los ESP32

---

## 🔧 Instalación Paso a Paso

### **1. Clonar el Repositorio**

```bash
git clone https://github.com/Cristestzzz/SmartHome.git
cd SmartHome
```

### **2. Instalar Python**

1. Descargar Python 3.10 o superior: https://www.python.org/downloads/
2. Durante la instalación: **✅ Marcar "Add Python to PATH"**
3. Verificar instalación:
   ```bash
   python --version
   ```

### **3. Instalar Mosquitto (MQTT Broker)**

1. Descargar desde: https://mosquitto.org/download/
2. Instalar (siguiente → siguiente → finalizar)
3. Verificar instalación:
   ```bash
   mosquitto -h
   ```

### **4. Instalar Dependencias Python**

```bash
cd servidor
pip install -r requirements_fastapi.txt
```

Si falla, instalar manualmente:
```bash
pip install fastapi uvicorn paho-mqtt websockets pydantic python-multipart jinja2 aiofiles
```

### **5. Obtener IP de esta Laptop**

```bash
ipconfig
```

Anota la **IPv4 Address** de tu red WiFi (ejemplo: `192.168.0.114`)

**Esta IP la necesitarás para configurar el ESP32**

---

## 🚀 Iniciar el Sistema

### **Terminal 1: Mosquitto**

```bash
mosquitto -v
```

Deberías ver:
```
mosquitto version 2.x starting
Opening ipv4 listen socket on port 1883.
```

### **Terminal 2: FastAPI**

```bash
cd SmartHome/servidor
python main.py
```

Deberías ver:
```
============================================================
🏠 SMARTHOME API - FASTAPI + MQTT + WEBSOCKET
============================================================
✓ Base de datos inicializada
✓ Conectando a MQTT broker: localhost:1883
✓ MQTT conectado exitosamente
✓ Suscrito a: casa/sensores/#
✓ FastAPI iniciado

📡 Iniciando servidor en http://0.0.0.0:8000
```

---

## ✅ Verificar que Funciona

### **1. Desde esta laptop:**

Abre en el navegador:
- Dashboard: http://localhost:8000
- Swagger API: http://localhost:8000/docs

### **2. Desde otra computadora en la misma red:**

- Dashboard: http://192.168.0.114:8000 (usa tu IP)

### **3. Verificar WebSocket:**

1. Abre http://localhost:8000
2. Presiona F12 (consola del navegador)
3. Deberías ver:
   ```
   🏠 Iniciando Dashboard Premium...
   🔌 Conectando WebSocket: ws://localhost:8000/ws
   ✓ WebSocket conectado
   ```

---

## 🔌 Configurar ESP32

### **1. Instalar Arduino IDE**

Si no lo tienes: https://www.arduino.cc/en/software

### **2. Instalar Librería MQTT**

Arduino IDE → Tools → Manage Libraries → Buscar: `PubSubClient` → Install

### **3. Configurar Código**

Abre: `SmartHome/firmware/esp32_receptor/esp32_receptor_mqtt.ino`

Edita estas líneas:

```cpp
// Líneas 18-20
const char* WIFI_SSID = "TU_WIFI";          // ← Cambiar
const char* WIFI_PASSWORD = "TU_PASSWORD";  // ← Cambiar

// Línea 23
const char* MQTT_SERVER = "192.168.0.114";  // ← Tu IP del paso 5
```

### **4. Subir al ESP32**

1. Conecta ESP32 por USB
2. Arduino IDE → Tools → Board → ESP32 Dev Module
3. Tools → Port → (selecciona tu puerto COM)
4. Click en Upload (→)

### **5. Verificar ESP32**

Abre Serial Monitor (115200 baud), deberías ver:

```
WiFi OK
IP: 192.168.0.XXX
Conectando MQTT...OK
✓ Suscrito a casa/actuadores/#
Sistema listo
```

---

## 🔥 Configurar Firewall (Importante)

Si no puedes acceder desde otra computadora:

1. Panel de Control → Firewall de Windows
2. Configuración avanzada → Reglas de entrada
3. Nueva regla → Puerto → TCP → 8000
4. Permitir conexión → Aplicar

---

## 🐛 Solución de Problemas

### **Error: "ModuleNotFoundError: No module named 'fastapi'"**
```bash
pip install fastapi uvicorn
```

### **Error: Mosquitto no conecta**
- Verifica que esté corriendo: `mosquitto -v`
- Verifica que no haya otro proceso en puerto 1883

### **Error: ESP32 no conecta a MQTT**
- Verifica la IP del servidor
- Verifica que estén en la misma red WiFi
- Revisa el firewall

### **Dashboard no carga**
- Verifica que FastAPI esté corriendo
- Verifica la URL: http://localhost:8000
- Revisa la consola del navegador (F12)

---

## 📚 URLs del Sistema

Una vez todo funcione:

- **Dashboard:** http://TU_IP:8000
- **Control Manual:** http://TU_IP:8000/control
- **Historial:** http://TU_IP:8000/historial
- **API Docs (Swagger):** http://TU_IP:8000/docs
- **Health Check:** http://TU_IP:8000/api/health

---

## ✅ Checklist Final

- [ ] Python instalado
- [ ] Mosquitto instalado
- [ ] Repositorio clonado
- [ ] Dependencias instaladas
- [ ] IP del servidor obtenida
- [ ] Mosquitto corriendo
- [ ] FastAPI corriendo
- [ ] Dashboard accesible
- [ ] Firewall configurado
- [ ] ESP32 configurado con IP correcta
- [ ] ESP32 conectado a MQTT
- [ ] WebSocket conectado en dashboard
- [ ] Sistema funcionando ✅

---

## 🎯 Resultado Esperado

Cuando todo esté funcionando:
- ✅ Dashboard actualiza en tiempo real (< 1 segundo)
- ✅ Comandos se ejecutan instantáneamente
- ✅ ESP32 publica datos por MQTT
- ✅ Sistema completamente funcional

**¡Listo para usar!** 🚀

---

## 📞 Soporte

Si tienes problemas, revisa:
- `servidor/STARTUP_GUIDE.md` - Guía de inicio detallada
- `servidor/mqtt_topics.md` - Documentación de topics MQTT
- Logs en las terminales de Mosquitto y FastAPI
