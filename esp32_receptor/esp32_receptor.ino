/*
 * ========================================
 * ESP32 RECEPTOR - SISTEMA COMPLETO
 * ========================================
 * Compatible con ESP32 core v2.x y v3.x
 * Compatible con ArduinoJson v7.x
 * 
 * - Recibe datos vía ESP-NOW
 * - Control automático por sensores
 * - Control manual desde servidor web
 * - Polling de comandos del servidor
 */

#include <esp_now.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACIÓN ====================

// WiFi - CAMBIAR ESTOS VALORES
const char* WIFI_SSID = "GAUTAMA";
const char* WIFI_PASSWORD = "gautama2024";

// URLs del servidor - CAMBIAR LA IP
const char* SERVER_URL_DATOS = "http://192.168.0.34:5000/api/datos/datos";
const char* SERVER_URL_COMANDOS = "http://192.168.0.34:5000/api/comandos";

// Pines
#define MOTOR_PIN 27      // Ventilador
#define BOMBA_PIN 26      // Bomba de agua

// Umbrales automáticos (se pueden actualizar desde servidor)
float TEMP_ACTIVACION = 30.0;
float TEMP_DESACTIVACION = 28.0;
int HUMEDAD_SUELO_SECO = 30;
int HUMEDAD_SUELO_HUMEDO = 70;

// Intervalos
#define ENVIO_SERVIDOR_INTERVALO 10000   // 10s
#define POLLING_COMANDOS_INTERVALO 5000  // 5s
#define TIMEOUT_SIN_DATOS 15000          // 15s

// ==================== VARIABLES GLOBALES ====================

typedef struct struct_message {
  float temperatura;
  float humedad;
  int humedad_suelo;
  unsigned long timestamp;
} struct_message;

struct_message datosRecibidos;

// Estado del sistema
String modoActual = "automatico";  // "automatico" o "manual"
bool motorActivo = false;
bool bombaActiva = false;
int servoAngulo = 90;

// Control de tiempo
unsigned long ultimoDatoRecibido = 0;
unsigned long ultimoEnvioServidor = 0;
unsigned long ultimoPollingComandos = 0;

bool wifiConectado = false;
bool datosDisponibles = false;

// ==================== FUNCIONES ====================

void conectarWiFi() {
  Serial.println("\n📡 Conectando a WiFi...");
  Serial.print("SSID: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_AP_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 20) {
    delay(500);
    Serial.print(".");
    intentos++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConectado = true;
    Serial.println("\n✓ WiFi conectado exitosamente");
    Serial.print("IP asignada: ");
    Serial.println(WiFi.localIP());
    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());
    Serial.print("⚠️  CANAL WiFi: ");
    Serial.println(WiFi.channel());
    Serial.println("   ← ANOTA ESTE CANAL para configurar EMISOR");
  } else {
    wifiConectado = false;
    Serial.println("\n✗ WiFi NO conectado");
    Serial.println("⚠️  VERIFICA:");
    Serial.print("   SSID: ");
    Serial.println(WIFI_SSID);
    Serial.println("   Password: [oculto]");
    Serial.println("   ¿Router encendido?");
  }
}

void controlarMotor(bool activar) {
  if (activar == motorActivo) return;
  
  if (activar) {
    digitalWrite(MOTOR_PIN, HIGH);
    motorActivo = true;
    Serial.println("🌀 MOTOR ENCENDIDO");
  } else {
    digitalWrite(MOTOR_PIN, LOW);
    motorActivo = false;
    Serial.println("⏹️  MOTOR APAGADO");
  }
}

void controlarBomba(bool activar) {
  if (activar == bombaActiva) return;
  
  if (activar) {
    digitalWrite(BOMBA_PIN, HIGH);
    bombaActiva = true;
    Serial.println("💧 BOMBA ENCENDIDA (Regando...)");
  } else {
    digitalWrite(BOMBA_PIN, LOW);
    bombaActiva = false;
    Serial.println("🚫 BOMBA APAGADA");
  }
}

void enviarDatosServidor() {
  if (!wifiConectado || !datosDisponibles) return;
  
  HTTPClient http;
  http.begin(SERVER_URL_DATOS);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  
  // Crear JSON usando ArduinoJson v7
  JsonDocument doc;  // En v7 se usa JsonDocument en lugar de StaticJsonDocument
  
  JsonObject sensores = doc["sensores"].to<JsonObject>();
  sensores["temperatura"] = datosRecibidos.temperatura;
  sensores["humedad"] = datosRecibidos.humedad;
  sensores["movimiento"] = 0;
  sensores["distancia"] = 0;
  sensores["humedad_suelo"] = datosRecibidos.humedad_suelo;
  
  JsonObject actuadores = doc["actuadores"].to<JsonObject>();
  actuadores["servo_angulo"] = servoAngulo;
  actuadores["ventilador_velocidad"] = 0;
  actuadores["bomba_activa"] = bombaActiva;
  
  JsonObject leds = actuadores["leds"].to<JsonObject>();
  leds["cuarto1"] = motorActivo;
  
  String json;
  serializeJson(doc, json);
  
  int httpCode = http.POST(json);
  
  if (httpCode == 200) {
    Serial.println("✓ Datos enviados al servidor");
  } else if (httpCode > 0) {
    Serial.print("⚠️  HTTP ");
    Serial.println(httpCode);
  } else {
    Serial.println("✗ Error HTTP");
  }
  
  http.end();
}

void consultarComandos() {
  if (!wifiConectado) return;
  
  HTTPClient http;
  http.begin(SERVER_URL_COMANDOS);
  http.setTimeout(3000);
  
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    
    // Parsear JSON usando ArduinoJson v7
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, payload);
    
    if (!error) {
      // Obtener modo
      if (doc.containsKey("modo")) {
        String nuevoModo = doc["modo"].as<String>();
        if (nuevoModo != modoActual) {
          modoActual = nuevoModo;
          Serial.print("🔄 Modo cambiado a: ");
          Serial.println(modoActual);
        }
      }
      
      // Obtener configuración de umbrales
      if (doc.containsKey("configuracion")) {
        JsonObject config = doc["configuracion"].as<JsonObject>();
        
        bool cambioConfig = false;
        
        if (config.containsKey("temp_activacion")) {
          float nuevoValor = config["temp_activacion"].as<float>();
          if (nuevoValor != TEMP_ACTIVACION) {
            TEMP_ACTIVACION = nuevoValor;
            cambioConfig = true;
          }
        }
        
        if (config.containsKey("temp_desactivacion")) {
          float nuevoValor = config["temp_desactivacion"].as<float>();
          if (nuevoValor != TEMP_DESACTIVACION) {
            TEMP_DESACTIVACION = nuevoValor;
            cambioConfig = true;
          }
        }
        
        if (config.containsKey("humedad_suelo_seco")) {
          int nuevoValor = config["humedad_suelo_seco"].as<int>();
          if (nuevoValor != HUMEDAD_SUELO_SECO) {
            HUMEDAD_SUELO_SECO = nuevoValor;
            cambioConfig = true;
          }
        }
        
        if (config.containsKey("humedad_suelo_humedo")) {
          int nuevoValor = config["humedad_suelo_humedo"].as<int>();
          if (nuevoValor != HUMEDAD_SUELO_HUMEDO) {
            HUMEDAD_SUELO_HUMEDO = nuevoValor;
            cambioConfig = true;
          }
        }
        
        if (cambioConfig) {
          Serial.println("\n⚙️  CONFIGURACIÓN ACTUALIZADA:");
          Serial.print("   Temp ON: ");
          Serial.print(TEMP_ACTIVACION);
          Serial.print("°C | Temp OFF: ");
          Serial.print(TEMP_DESACTIVACION);
          Serial.println("°C");
          Serial.print("   Suelo SECO: ");
          Serial.print(HUMEDAD_SUELO_SECO);
          Serial.print("% | Suelo HÚMEDO: ");
          Serial.print(HUMEDAD_SUELO_HUMEDO);
          Serial.println("%\n");
        }
      }
      
      // Si está en modo manual, aplicar comandos
      if (modoActual == "manual" && doc.containsKey("comandos")) {
        JsonObject comandos = doc["comandos"].as<JsonObject>();
        
        // Ventilador
        if (comandos.containsKey("ventilador")) {
          bool estado = comandos["ventilador"].as<bool>();
          controlarMotor(estado);
        }
        
        // Bomba
        if (comandos.containsKey("bomba")) {
          bool estado = comandos["bomba"].as<bool>();
          controlarBomba(estado);
        }
        
        // Servo
        if (comandos.containsKey("servo")) {
          servoAngulo = comandos["servo"].as<int>();
          Serial.print("🔄 Servo: ");
          Serial.print(servoAngulo);
          Serial.println("°");
        }
      }
    }
  }
  
  http.end();
}

void controlAutomatico() {
  if (!datosDisponibles) return;
  
  // Control ventilador por temperatura
  if (datosRecibidos.temperatura >= TEMP_ACTIVACION) {
    controlarMotor(true);
  } else if (datosRecibidos.temperatura <= TEMP_DESACTIVACION) {
    controlarMotor(false);
  }
  
  // Control bomba por humedad del suelo
  if (datosRecibidos.humedad_suelo < HUMEDAD_SUELO_SECO) {
    controlarBomba(true);
  } else if (datosRecibidos.humedad_suelo > HUMEDAD_SUELO_HUMEDO) {
    controlarBomba(false);
  }
}

// ==================== CALLBACKS ESP-NOW ====================

#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
void OnDataRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len) {
#else
void OnDataRecv(const uint8_t *mac, const uint8_t *incomingData, int len) {
#endif
  
  memcpy(&datosRecibidos, incomingData, sizeof(datosRecibidos));
  datosDisponibles = true;
  ultimoDatoRecibido = millis();
  
  // Mostrar datos
  Serial.print("📊 Temp: ");
  Serial.print(datosRecibidos.temperatura, 1);
  Serial.print("°C | Hum: ");
  Serial.print(datosRecibidos.humedad, 1);
  Serial.print("% | Suelo: ");
  Serial.print(datosRecibidos.humedad_suelo);
  Serial.print("% | Modo: ");
  Serial.println(modoActual);
  
  // Aplicar control según modo
  if (modoActual == "automatico") {
    controlAutomatico();
  }
  // En modo manual, los comandos se aplican desde consultarComandos()
}

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n==================================================");
  Serial.println("     ESP32 RECEPTOR - SISTEMA COMPLETO");
  Serial.println("==================================================");
  
  // Configurar pines
  pinMode(MOTOR_PIN, OUTPUT);
  pinMode(BOMBA_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, LOW);
  digitalWrite(BOMBA_PIN, LOW);
  Serial.println("✓ Actuadores inicializados (OFF)");
  
  // Conectar WiFi
  conectarWiFi();
  
  // Obtener MAC
  Serial.println("\n--------------------------------------------------");
  Serial.print("Mi MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.println("← Configura esta MAC en el EMISOR");
  Serial.println("--------------------------------------------------");
  
  // Inicializar ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("✗ Error inicializando ESP-NOW");
    while(1) { delay(1000); }
  }
  Serial.println("✓ ESP-NOW inicializado");
  
  // Registrar callback
  esp_now_register_recv_cb(OnDataRecv);
  
  Serial.println("\n✓ Sistema listo");
  Serial.println("Modo: AUTOMÁTICO (default)");
  Serial.println("Esperando datos del EMISOR...");
  Serial.println("==================================================\n");
  
  ultimoDatoRecibido = millis();
  ultimoEnvioServidor = millis();
  ultimoPollingComandos = millis();
}

// ==================== LOOP ====================

void loop() {
  unsigned long ahora = millis();
  
  // Enviar datos al servidor cada 10s
  if (wifiConectado && (ahora - ultimoEnvioServidor >= ENVIO_SERVIDOR_INTERVALO)) {
    if (datosDisponibles) {
      enviarDatosServidor();
    }
    ultimoEnvioServidor = ahora;
  }
  
  // Consultar comandos del servidor cada 5s
  if (wifiConectado && (ahora - ultimoPollingComandos >= POLLING_COMANDOS_INTERVALO)) {
    consultarComandos();
    ultimoPollingComandos = ahora;
  }
  
  // Timeout de seguridad
  if ((motorActivo || bombaActiva) && (ahora - ultimoDatoRecibido > TIMEOUT_SIN_DATOS)) {
    Serial.println("\n⚠️  TIMEOUT: Sin datos del EMISOR");
    controlarMotor(false);
    controlarBomba(false);
    datosDisponibles = false;
    ultimoDatoRecibido = ahora;
  }
  
  // Reconectar WiFi si se cae
  if (WiFi.status() != WL_CONNECTED && wifiConectado) {
    Serial.println("\n⚠️  WiFi desconectado");
    wifiConectado = false;
    conectarWiFi();
  }
  
  delay(100);
}
