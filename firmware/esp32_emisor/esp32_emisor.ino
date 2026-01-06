/*
 * ========================================
 * ESP32 EMISOR - SENSOR DHT11
 * ========================================
 * Compatible con ESP32 core v2.x y v3.x
 * 
 * Hardware:
 * - DHT11 en GPIO4
 * - LED status en GPIO2
 */

#include <esp_now.h>
#include <WiFi.h>
#include <DHT.h>
#include <esp_wifi.h>  // ← AGREGAR ESTO

// ==================== CONFIGURACIÓN ====================

// Pin del DHT11
#define DHT_PIN 4
#define DHT_TYPE DHT11

// Pin del sensor de humedad del suelo (analógico)
#define HUMEDAD_SUELO_PIN 35  // ADC1 - más estable

// Calibración del sensor de humedad (ajustar según tu sensor)
#define VALOR_SECO 3200    // Valor cuando el suelo está seco
#define VALOR_HUMEDO 1450  // Valor cuando el suelo está húmedo

// Pin del LED
#define LED_PIN 2

// MAC del ESP32 RECEPTOR - CONFIGURADO
uint8_t receiverMAC[] = {0xEC, 0x64, 0xC9, 0x91, 0xBD, 0x3C};

// IMPORTANTE: Configurar el canal del WiFi del RECEPTOR
// El RECEPTOR está en el canal del router WiFi
// Cambia este número por el que veas en el RECEPTOR
#define WIFI_CHANNEL 5  // ← CAMBIAR POR EL CANAL DEL RECEPTOR

// Intervalo de envío
#define ENVIO_INTERVALO 3000  // 3 segundos

// ==================== ESTRUCTURA DE DATOS ====================

DHT dht(DHT_PIN, DHT_TYPE);

typedef struct struct_message {
  float temperatura;
  float humedad;
  int humedad_suelo;  // 0-100% (0=seco, 100=húmedo)
  unsigned long timestamp;
} struct_message;

struct_message datosEnviar;

unsigned long ultimoEnvio = 0;
int contadorEnvios = 0;

// ==================== CALLBACKS (COMPATIBLE) ====================

// Callback compatible con ESP32 core v2.x y v3.x
#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
// Para versión 3.x
void OnDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
#else
// Para versión 2.x
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
  if (status == ESP_NOW_SEND_SUCCESS) {
    Serial.println("✓");
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
  } else {
    Serial.println("✗");
  }
}

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n==================================================");
  Serial.println("     ESP32 EMISOR - SENSOR DHT11");
  Serial.println("==================================================");
  
  // LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // DHT11
  dht.begin();
  Serial.println("✓ DHT11 inicializado");
  
  // Sensor de humedad del suelo
  // GPIO35 es solo entrada, no requiere pinMode
  Serial.println("✓ Sensor humedad suelo inicializado (GPIO35)");
  
  // WiFi en modo estación
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  
  // Forzar inicialización
  WiFi.begin("dummy", "dummy");
  delay(1000);
  WiFi.disconnect();
  delay(500);
  
  // Configurar para ESP-NOW
  WiFi.mode(WIFI_STA);
  
  // IMPORTANTE: Configurar el mismo canal que el RECEPTOR
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);
  
  Serial.print("Mi MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.print("Canal WiFi: ");
  Serial.println(WiFi.channel());
  Serial.println("--------------------------------------------------");
  
  // ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("✗ Error inicializando ESP-NOW");
    while(1) { delay(1000); }
  }
  Serial.println("✓ ESP-NOW inicializado");
  
  // Registrar callback
  esp_now_register_send_cb(OnDataSent);
  
  // Registrar peer (receptor)
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, receiverMAC, 6);
  peerInfo.channel = WIFI_CHANNEL;  // Usar el mismo canal
  peerInfo.encrypt = false;
  peerInfo.ifidx = WIFI_IF_STA;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("✗ Error al agregar peer");
    while(1) { delay(1000); }
  }
  
  Serial.println("✓ Peer agregado");
  Serial.println("\n📡 Enviando datos cada 3 segundos...");
  Serial.println("==================================================\n");
}

// ==================== LOOP ====================

void loop() {
  unsigned long ahora = millis();
  
  if (ahora - ultimoEnvio >= ENVIO_INTERVALO) {
    
    // Leer DHT11
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();
    
    // Leer sensor de humedad del suelo con promedio de 10 muestras
    long sumaLecturas = 0;
    int muestras = 10;
    
    for(int i = 0; i < muestras; i++) {
      sumaLecturas += analogRead(HUMEDAD_SUELO_PIN);
      delay(10);
    }
    
    int lecturaPromedio = sumaLecturas / muestras;
    int humedadSuelo = map(lecturaPromedio, VALOR_SECO, VALOR_HUMEDO, 0, 100);
    humedadSuelo = constrain(humedadSuelo, 0, 100);
    
    if (isnan(temp) || isnan(hum)) {
      Serial.println("✗ Error al leer DHT11");
    } else {
      
      // Preparar datos
      datosEnviar.temperatura = temp;
      datosEnviar.humedad = hum;
      datosEnviar.humedad_suelo = humedadSuelo;
      datosEnviar.timestamp = millis();
      
      // Mostrar
      Serial.print("📊 Temp: ");
      Serial.print(temp, 1);
      Serial.print("°C | Hum: ");
      Serial.print(hum, 1);
      Serial.print("% | Suelo: ");
      Serial.print(humedadSuelo);
      Serial.print("% ");
      
      // Indicar estado del suelo
      if (humedadSuelo < 30) {
        Serial.print("💧SECO ");
      } else if (humedadSuelo > 70) {
        Serial.print("💦HÚMEDO ");
      } else {
        Serial.print("✓OK ");
      }
      
      Serial.print("(Raw:");
      Serial.print(lecturaPromedio);
      Serial.print(") | ");
      
      // Enviar
      esp_err_t result = esp_now_send(receiverMAC, (uint8_t *) &datosEnviar, sizeof(datosEnviar));
      
      if (result != ESP_OK) {
        Serial.println("✗ Error al enviar");
      }
      
      contadorEnvios++;
      if (contadorEnvios % 10 == 0) {
        Serial.println("\n[" + String(contadorEnvios) + " envíos completados]");
      }
    }
    
    ultimoEnvio = ahora;
  }
}
