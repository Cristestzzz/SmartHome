/*
 * ========================================
 * ESP32 RECEPTOR - MQTT VERSION
 * ========================================
 * Migrado de HTTP a MQTT para comunicación en tiempo real
 * 
 * Hardware:
 * - Motor (Ventilador) en GPIO 27
 * - Bomba en GPIO 26
 * - LEDs en GPIO 33, 12, 14
 */

#include <esp_now.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACIÓN ====================

const char* WIFI_SSID = "RANZA";
const char* WIFI_PASSWORD = "23855951";

// Servidor MQTT
const char* MQTT_SERVER = "192.168.0.107";
const int MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "ESP32_Receptor";

// Pines
#define MOTOR_PIN 27
#define BOMBA_PIN 26
#define LED_CUARTO1 33
#define LED_CUARTO2 12
#define LED_CUARTO3 14

// Umbrales (se actualizan por MQTT)
float TEMP_ACTIVACION = 30.0;
float TEMP_DESACTIVACION = 28.0;
int HUMEDAD_SUELO_SECO = 30;
int HUMEDAD_SUELO_HUMEDO = 70;

// Timeouts
#define TIMEOUT_SIN_DATOS 15000
#define MQTT_RECONNECT_DELAY 5000

// ==================== VARIABLES GLOBALES ====================

typedef struct struct_message {
  float temperatura;
  float humedad;
  int humedad_suelo;
  unsigned long timestamp;
} struct_message;

struct_message datosRecibidos;

String modoActual = "automatico";
bool motorActivo = false;
bool bombaActiva = false;
int servoAngulo = 90;

bool ledCuarto1 = false;
bool ledCuarto2 = false;
bool ledCuarto3 = false;

unsigned long ultimoDatoRecibido = 0;
unsigned long ultimoReconectMQTT = 0;

bool wifiConectado = false;
bool mqttConectado = false;
bool datosDisponibles = false;

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ==================== FUNCIONES WiFi ====================

void conectarWiFi() {
  Serial.println("WiFi conectando...");
  // Usar WIFI_AP_STA como en el código que funciona
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
    Serial.println("\nWiFi OK");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Canal: ");
    Serial.println(WiFi.channel());
  } else {
    wifiConectado = false;
    Serial.println("\nWiFi FAIL");
  }
}

// ==================== FUNCIONES MQTT ====================

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Convertir payload a string
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("📨 MQTT: ");
  Serial.print(topic);
  Serial.print(" = ");
  Serial.println(message);
  
  // Procesar según topic
  String topicStr = String(topic);
  
  // Actuadores
  if (topicStr == "casa/actuadores/ventilador") {
    controlarMotor(message == "ON");
  }
  else if (topicStr == "casa/actuadores/bomba") {
    controlarBomba(message == "ON");
  }
  else if (topicStr == "casa/actuadores/servo") {
    servoAngulo = message.toInt();
    Serial.print("Servo: ");
    Serial.println(servoAngulo);
  }
  else if (topicStr == "casa/actuadores/leds/cuarto1") {
    controlarLED(LED_CUARTO1, ledCuarto1, message == "ON", "Cuarto1");
  }
  else if (topicStr == "casa/actuadores/leds/cuarto2") {
    controlarLED(LED_CUARTO2, ledCuarto2, message == "ON", "Cuarto2");
  }
  else if (topicStr == "casa/actuadores/leds/cuarto3") {
    controlarLED(LED_CUARTO3, ledCuarto3, message == "ON", "Cuarto3");
  }
  // Sistema
  else if (topicStr == "casa/sistema/modo") {
    if (message != modoActual) {
      modoActual = message;
      Serial.print("Modo: ");
      Serial.println(modoActual);
    }
  }
  else if (topicStr == "casa/sistema/config") {
    // Parsear JSON de configuración
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, message);
    if (!error) {
      if (doc.containsKey("temp_activacion")) {
        TEMP_ACTIVACION = doc["temp_activacion"];
      }
      if (doc.containsKey("temp_desactivacion")) {
        TEMP_DESACTIVACION = doc["temp_desactivacion"];
      }
      if (doc.containsKey("humedad_suelo_seco")) {
        HUMEDAD_SUELO_SECO = doc["humedad_suelo_seco"];
      }
      if (doc.containsKey("humedad_suelo_humedo")) {
        HUMEDAD_SUELO_HUMEDO = doc["humedad_suelo_humedo"];
      }
      Serial.println("CONFIG ACTUALIZADA");
    }
  }
}

void conectarMQTT() {
  if (!wifiConectado) return;
  
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  
  Serial.print("Conectando MQTT...");
  
  if (mqttClient.connect(MQTT_CLIENT_ID)) {
    mqttConectado = true;
    Serial.println("OK");
    
    // Suscribirse a topics
    mqttClient.subscribe("casa/actuadores/#");
    mqttClient.subscribe("casa/sistema/#");
    
    Serial.println("✓ Suscrito a casa/actuadores/#");
    Serial.println("✓ Suscrito a casa/sistema/#");
  } else {
    mqttConectado = false;
    Serial.print("FAIL, rc=");
    Serial.println(mqttClient.state());
  }
}

void publicarSensoresMQTT() {
  if (!mqttConectado || !datosDisponibles) return;
  
  char temp[10], hum[10], suelo[10];
  
  // Convertir valores a strings
  dtostrf(datosRecibidos.temperatura, 4, 1, temp);
  dtostrf(datosRecibidos.humedad, 4, 1, hum);
  sprintf(suelo, "%d", datosRecibidos.humedad_suelo);
  
  // Publicar cada sensor
  mqttClient.publish("casa/sensores/temperatura", temp);
  mqttClient.publish("casa/sensores/humedad", hum);
  mqttClient.publish("casa/sensores/humedad_suelo", suelo);
  
  Serial.println("✓ Sensores publicados por MQTT");
}

// ==================== CONTROL DE ACTUADORES ====================

void controlarMotor(bool activar) {
  if (activar == motorActivo) return;
  digitalWrite(MOTOR_PIN, activar ? HIGH : LOW);
  motorActivo = activar;
  Serial.println(activar ? "MOTOR ON" : "MOTOR OFF");
}

void controlarBomba(bool activar) {
  if (activar == bombaActiva) return;
  digitalWrite(BOMBA_PIN, activar ? HIGH : LOW);
  bombaActiva = activar;
  Serial.println(activar ? "BOMBA ON" : "BOMBA OFF");
}

void controlarLED(int pin, bool &estado, bool activar, const char* nombre) {
  if (activar == estado) return;
  digitalWrite(pin, activar ? HIGH : LOW);
  estado = activar;
  Serial.print("LED ");
  Serial.print(nombre);
  Serial.println(activar ? " ON" : " OFF");
}

// ==================== CONTROL AUTOMÁTICO ====================

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

// ==================== ESP-NOW ====================

#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
void OnDataRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len) {
#else
void OnDataRecv(const uint8_t *mac, const uint8_t *incomingData, int len) {
#endif
  
  memcpy(&datosRecibidos, incomingData, sizeof(datosRecibidos));
  datosDisponibles = true;
  ultimoDatoRecibido = millis();
  
  Serial.print("T:");
  Serial.print(datosRecibidos.temperatura, 1);
  Serial.print("C H:");
  Serial.print(datosRecibidos.humedad, 1);
  Serial.print("% S:");
  Serial.print(datosRecibidos.humedad_suelo);
  Serial.println("%");
  
  // Publicar por MQTT
  publicarSensoresMQTT();
  
  // Control automático si está en modo automático
  if (modoActual == "automatico") {
    controlAutomatico();
  }
}

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("\n=== ESP32 RECEPTOR - MQTT VERSION ===");

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

  Serial.println("Pines OK");

  // Conectar WiFi
  conectarWiFi();

  // Conectar MQTT
  if (wifiConectado) {
    conectarMQTT();
  }

  // ESP-NOW
  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW FAIL");
    while(1);
  }

  esp_now_register_recv_cb(OnDataRecv);

  Serial.println("Sistema listo");
  Serial.print("Modo: ");
  Serial.println(modoActual);

  if (wifiConectado) {
    Serial.print("Canal WiFi: ");
    Serial.println(WiFi.channel());
    Serial.println("IMPORTANTE: Configura el ESP32 EMISOR");
    Serial.print("            con WIFI_CHANNEL = ");
    Serial.println(WiFi.channel());
  }

  ultimoDatoRecibido = millis();
  ultimoReconectMQTT = millis();
}

// ==================== LOOP ====================

void loop() {
  unsigned long ahora = millis();
  
  yield();
  
  // Mantener conexión MQTT
  if (mqttConectado) {
    mqttClient.loop();
  } else {
    // Intentar reconectar cada 5 segundos
    if (ahora - ultimoReconectMQTT >= MQTT_RECONNECT_DELAY) {
      conectarMQTT();
      ultimoReconectMQTT = ahora;
    }
  }
  
  yield();
  
  // Timeout de seguridad
  if ((motorActivo || bombaActiva) && (ahora - ultimoDatoRecibido > TIMEOUT_SIN_DATOS)) {
    Serial.println("TIMEOUT");
    controlarMotor(false);
    controlarBomba(false);
    datosDisponibles = false;
  }
  
  yield();

  // Verificar WiFi (como en el código antiguo)
  if (WiFi.status() != WL_CONNECTED && wifiConectado) {
    wifiConectado = false;
    mqttConectado = false;
    conectarWiFi();
    if (wifiConectado) {
      conectarMQTT();
    }
  }

  delay(100);
}
