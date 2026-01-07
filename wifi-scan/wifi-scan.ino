#include <WiFi.h>
#include <ESP32Servo.h>

// --- PIN DEFINITIONS ---
const int SERVO_PIN = 18;
const int LED_GREEN = 26;
const int LED_RED = 27;
const int BUTTON_PIN = 14;

// --- OBJECTS & VARIABLES ---
Servo lockServo;
bool isLocked = true;
unsigned long unlockTime = 0;
const int UNLOCK_DURATION = 5000; // 5 seconds in milliseconds

void setup() {
  Serial.begin(115200);
  
  // 1. Setup Servo
  lockServo.attach(SERVO_PIN);
  
  // 2. Setup LEDs
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  
  // 3. Setup Button (Using Internal Pullup)
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // 4. Initial State: LOCKED
  lock();
  
  Serial.println("System Initialized: LOCKED State");
}

void loop() {
  // --- BUTTON TEST LOGIC ---
  // If button is pressed (LOW because of pullup) and currently locked
  if (digitalRead(BUTTON_PIN) == LOW && isLocked) {
    unlock();
  }

  // --- AUTO-RELOCK LOGIC ---
  // If unlocked and 5 seconds have passed
  if (!isLocked && (millis() - unlockTime > UNLOCK_DURATION)) {
    lock();
  }

  delay(50); // Small delay for stability
}

// Function to UNLOCK the vault
void unlock() {
  Serial.println("Action: UNLOCKING...");
  lockServo.write(90);      // Rotate to 90 degrees
  digitalWrite(LED_GREEN, HIGH); // Green ON
  digitalWrite(LED_RED, LOW);    // Red OFF
  isLocked = false;
  unlockTime = millis();    // Record the time we unlocked
}

// Function to LOCK the vault
void lock() {
  Serial.println("Action: LOCKING...");
  lockServo.write(0);       // Rotate to 0 degrees
  digitalWrite(LED_GREEN, LOW);  // Green OFF
  digitalWrite(LED_RED, HIGH);   // Red ON
  isLocked = true;
}