#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>

// --- WIFI ---
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// --- TUNNEL LINK ---
// MAKE SURE THIS IS CORRECT AND ALIVE!
const char* serverUrl = "http://62740269c24c52.lhr.life/Mobius/SmartLock/data";

// --- PINS ---
const int SERVO_PIN = 18;
const int LED_GREEN = 26;
const int LED_RED = 27;
const int BUTTON_PIN = 14;

Servo lockServo;
bool isLocked = true;
unsigned long lastCheckTime = 0;
unsigned long unlockTime = 0;

void setup() {
  Serial.begin(115200);

  lockServo.attach(SERVO_PIN);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password, 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.print(".");
  }
  Serial.println(" Connected!");
  
  lock(); 
}

void loop() {
  // 1. MANUAL BUTTON
  if (digitalRead(BUTTON_PIN) == LOW && isLocked) {
    unlock();
    sendDataToMobius("UNLOCKED");
  }

  // 2. REMOTE CHECK (Every 3 Seconds)
  if (millis() - lastCheckTime > 3000) {
    checkRemoteStatus();
    lastCheckTime = millis();
  }

  // 3. AUTO-RELOCK
  if (!isLocked && (millis() - unlockTime > 5000)) {
    lock();
    sendDataToMobius("LOCKED");
  }
  
  delay(50);
}

void unlock() {
  if(isLocked){
    Serial.println("Action: UNLOCKING VAULT...");
    lockServo.write(90);
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, LOW);
    isLocked = false;
    unlockTime = millis();
  }
}

void lock() {
  if(!isLocked){
    Serial.println("Action: LOCKING VAULT...");
    lockServo.write(0);
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    isLocked = true;
  }
}

void sendDataToMobius(String status) {
  if(WiFi.status() == WL_CONNECTED){
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("X-M2M-RI", "12345");
    http.addHeader("X-M2M-Origin", "S");
    http.addHeader("Content-Type", "application/vnd.onem2m-res+json; ty=4");
    String requestBody = "{\"m2m:cin\": {\"con\": \"" + status + "\"}}";
    http.POST(requestBody);
    http.end();
  }
}

// --- THE DEBUGGING CHECKER ---
void checkRemoteStatus() {
  if(WiFi.status() == WL_CONNECTED){
    HTTPClient http;
    
    // Add /la to get the latest data
    String checkUrl = String(serverUrl) + "/la";
    
    // DEBUG: Print what we are checking
    Serial.print("Checking: ");
    Serial.println(checkUrl);
    
    http.begin(checkUrl);
    http.addHeader("X-M2M-RI", "12345");
    http.addHeader("X-M2M-Origin", "S");
    http.addHeader("Accept", "application/json");
    
    int httpCode = http.GET();
    
    // DEBUG: Print the result code
    Serial.print("Result Code: ");
    Serial.println(httpCode);
    
    if (httpCode > 0) {
      String payload = http.getString();
      // DEBUG: Print the data from server
      Serial.println("Data: " + payload);
      
      if (payload.indexOf("UNLOCKED") > 0) {
         Serial.println("COMMAND FOUND: UNLOCKING!");
         unlock(); 
      }
    } else {
      Serial.print("Error: ");
      Serial.println(http.errorToString(httpCode));
    }
    http.end();
    Serial.println("-----------------------");
  }
}