/*
 * ========================================
 * ESP32 RECEPTOR - CON 5 LEDs
 * ========================================
 * Compatible con ESP32 core v2.x y v3.x
 * Compatible con ArduinoJson v7.x
 * 
 * Incluye:
 * - 5 LEDs controlables desde web
 * - Control manual/automático
 * - Configuración dinámica
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
const char* SERVER_URL_DATOS = "http://192.168.0.5:5000/api/datos/datos";
const char* SERVER_URL_COMANDOS = "http://192.168.0.5:5000/api/comandos";

// Pines
#define MOTOR_PIN 27      // Ventilador
#define BOMBA_PIN 26      // Bomba de agua

// LEDs - 3 LEDs controlables
#define LED_CUARTO1 33
#define LED_CUARTO2 12
#define LED_CUARTO3 14

// Umbrales automáticos
float TEMP_ACTIVACION = 30.0;
float TEMP_DESACTIVACION = 28.0;
int HUMEDAD_SUELO_SECO = 30;
int HUMEDAD_SUELO_HUMEDO = 70;

// Intervalos
#define ENVIO_SERVIDOR_INTERVALO 10000
#define POLLING_COMANDOS_INTERVALO 5000
#define TIMEOUT_SIN_DATOS 15000

// ==================== VARIABLES GLOBALES ====================

typedef struct struct_message {
  float temperatura;
  float humedad;
  int humedad_suelo;
  unsigned long timestamp;
} struct_message;

struct_message datosRecibidos;

// Estado del sistema
String modoActual = "automatico";
bool motorActivo = false;
bool bombaActiva = false;
int servoAngulo = 90;

// Estado de LEDs
bool ledCuarto1 = false;
bool ledCuarto2 = false;
bool ledCuarto3 = false;

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
    Serial.print("⚠️  CANAL WiFi: ");
    Serial.println(WiFi.channel());
  } else {
    wifiConectado = false;
    Serial.println("\n✗ WiFi NO conectado");
  }
}

void controlarMotor(bool activar) {
  if (activar == motorActivo) return;
  
  digitalWrite(MOTOR_PIN, activar ? HIGH : LOW);
  motorActivo = activar;
  Serial.println(activar ? "🌀 MOTOR ENCENDIDO" : "⏹️  MOTOR APAGADO");
}

void controlarBomba(bool activar) {
  if (activar == bombaActiva) return;
  
  digitalWrite(BOMBA_PIN, activar ? HIGH : LOW);
  bombaActiva = activar;
  Serial.println(activar ? "💧 BOMBA ENCENDIDA" : "🚫 BOMBA APAGADA");
}

void controlarLED(int pin, bool &estado, bool activar, const char* nombre) {
  if (activar == estado) return;
  
  digitalWrite(pin, activar ? HIGH : LOW);
  estado = activar;
  
  Serial.print("💡 LED ");
  Serial.print(nombre);
  Serial.println(activar ? " ON" : " OFF");
}

void enviarDatosServidor() {
  if (!wifiConectado || !datosDisponibles) return;
  
  HTTPClient http;
  http.begin(SERVER_URL_DATOS);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  
  JsonDocument doc;
  
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
  leds["cuarto1"] = ledCuarto1;
  leds["cuarto2"] = ledCuarto2;
  leds["cuarto3"] = ledCuarto3;
  
  String json;
  serializeJson(doc, json);
  
  int httpCode = http.POST(json);
  
  if (httpCode == 200) {
    Serial.println("✓ Datos enviados");
  } else if (httpCode > 0) {
    Serial.print("⚠️  HTTP ");
    Serial.println(httpCode);
  } else {
    Serial.println("✗ Error conexión servidor");
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
    
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, payload);
    
    if (!error) {
      
      // Obtener modo
      if (doc.containsKey("modo")) {
        String nuevoModo = doc["modo"].as<String>();
        if (nuevoModo != modoActual) {
          modoActual = nuevoModo;
          Serial.print("🔄 Modo: ");
          Serial.println(modoActual);
        }
      }
      
      // Obtener configuración
      if (doc.containsKey("configuracion")) {
        JsonObject config = doc["configuracion"].as<JsonObject>();
        bool cambio = false;
        
        if (config.containsKey("temp_activacion")) {
          float val = config["temp_activacion"].as<float>();
          if (val != TEMP_ACTIVACION) {
            TEMP_ACTIVACION = val;
            cambio = true;
          }
        }
        
        if (config.containsKey("temp_desactivacion")) {
          float val = config["temp_desactivacion"].as<float>();
          if (val != TEMP_DESACTIVACION) {
            TEMP_DESACTIVACION = val;
            cambio = true;
          }
        }
        
        if (config.containsKey("humedad_suelo_seco")) {
          int val = config["humedad_suelo_seco"].as<int>();
          if (val != HUMEDAD_SUELO_SECO) {
            HUMEDAD_SUELO_SECO = val;
            cambio = true;
          }
        }
        
        if (config.containsKey("humedad_suelo_humedo")) {
          int val = config["humedad_suelo_humedo"].as<int>();
          if (val != HUMEDAD_SUELO_HUMEDO) {
            HUMEDAD_SUELO_HUMEDO = val;
            cambio = true;
          }
        }
        
        if (cambio) {
          Serial.println("\n⚙️  CONFIG ACTUALIZADA:");
          Serial.print("   Temp: ");
          Serial.print(TEMP_ACTIVACION);
          Serial.print("°C / ");
          Serial.print(TEMP_DESACTIVACION);
          Serial.println("°C");
          Serial.print("   Suelo: ");
          Serial.print(HUMEDAD_SUELO_SECO);
          Serial.print("% / ");
          Serial.print(HUMEDAD_SUELO_HUMEDO);
          Serial.println("%\n");
        }
      }
      
      // Comandos manuales (solo ventilador, bomba, servo)
      if (modoActual == "manual" && doc.containsKey("comandos")) {
        JsonObject comandos = doc["comandos"].as<JsonObject>();
        
        if (comandos.containsKey("ventilador")) {
          controlarMotor(comandos["ventilador"].as<bool>());
        }
        
        if (comandos.containsKey("bomba")) {
          controlarBomba(comandos["bomba"].as<bool>());
        }
        
        if (comandos.containsKey("servo")) {
          servoAngulo = comandos["servo"].as<int>();
        }
      }
      
      // LEDs SIEMPRE controlables (independiente del modo)
      if (doc.containsKey("comandos")) {
        JsonObject comandos = doc["comandos"].as<JsonObject>();
        
        if (comandos.containsKey("leds")) {
          JsonObject leds = comandos["leds"].as<JsonObject>();
          
          if (leds.containsKey("cuarto1")) {
            controlarLED(LED_CUARTO1, ledCuarto1, leds["cuarto1"].as<bool>(), "Cuarto1");
          }
          if (leds.containsKey("cuarto2")) {
            controlarLED(LED_CUARTO2, ledCuarto2, leds["cuarto2"].as<bool>(), "Cuarto2");
          }
          if (leds.containsKey("cuarto3")) {
            controlarLED(LED_CUARTO3, ledCuarto3, leds["cuarto3"].as<bool>(), "Cuarto3");
          }
        }
      }
    }
  }
  
  http.end();
}

void controlAutomatico() {
  if (!datosDisponibles) return;
  
  if (datosRecibidos.temperatura >= TEMP_ACTIVACION) {
    controlarMotor(true);
  } else if (datosRecibidos.temperatura <= TEMP_DESACTIVACION) {
    controlarMotor(false);
  }
  
  if (datosRecibidos.humedad_suelo < HUMEDAD_SUELO_SECO) {
    controlarBomba(true);
  } else if (datosRecibidos.humedad_suelo > HUMEDAD_SUELO_HUMEDO) {
    controlarBomba(false);
  }
}

#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
void OnDataRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len) {
#else
void OnDataRecv(const uint8_t *mac, const uint8_t *incomingData, int len) {
#endif
  
  memcpy(&datosRecibidos, incomingData, sizeof(datosRecibidos));
  datosDisponibles = true;
  ultimoDatoRecibido = millis();
  
  Serial.print("📊 ");
  Serial.print(datosRecibidos.temperatura, 1);
  Serial.print("°C | ");
  Serial.print(datosRecibidos.humedad, 1);
  Serial.print("% | S:");
  Serial.print(datosRecibidos.humedad_suelo);
  Serial.println("%");
  
  if (modoActual == "automatico") {
    controlAutomatico();
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n==== ESP32 RECEPTOR - 5 LEDs ====");
  
  // Pines actuadores
  pinMode(MOTOR_PIN, OUTPUT);
  pinMode(BOMBA_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, LOW);
  digitalWrite(BOMBA_PIN, LOW);
  
  // Pines LEDs
  pinMode(LED_CUARTO1, OUTPUT);
  pinMode(LED_CUARTO2, OUTPUT);
  pinMode(LED_CUARTO3, OUTPUT);
  digitalWrite(LED_CUARTO1, LOW);
  digitalWrite(LED_CUARTO2, LOW);
  digitalWrite(LED_CUARTO3, LOW);
  
  Serial.println("✓ Actuadores y LEDs inicializados");
  
  conectarWiFi();
  
  Serial.print("Mi MAC: ");
  Serial.println(WiFi.macAddress());
  
  if (esp_now_init() != ESP_OK) {
    Serial.println("✗ Error ESP-NOW");
    while(1);
  }
  
  esp_now_register_recv_cb(OnDataRecv);
  
  Serial.println("✓ Sistema listo\n");
  
  ultimoDatoRecibido = millis();
  ultimoEnvioServidor = millis();
  ultimoPollingComandos = millis();
}

void loop() {
  unsigned long ahora = millis();
  
  if (wifiConectado && (ahora - ultimoEnvioServidor >= ENVIO_SERVIDOR_INTERVALO)) {
    if (datosDisponibles) {
      enviarDatosServidor();
    }
    ultimoEnvioServidor = ahora;
  }
  
  if (wifiConectado && (ahora - ultimoPollingComandos >= POLLING_COMANDOS_INTERVALO)) {
    consultarComandos();
    ultimoPollingComandos = ahora;
  }
  
  if ((motorActivo || bombaActiva) && (ahora - ultimoDatoRecibido > TIMEOUT_SIN_DATOS)) {
    Serial.println("⚠️  TIMEOUT");
    controlarMotor(false);
    controlarBomba(false);
    datosDisponibles = false;
  }
  
  if (WiFi.status() != WL_CONNECTED && wifiConectado) {
    wifiConectado = false;
    conectarWiFi();
  }
  
  delay(100);
}
