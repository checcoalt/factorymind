#include "DHT.h"

// Impostazioni sensore
#define DHTPIN 4        // Pin collegato al segnale del DHT22
#define DHTTYPE DHT22   // Tipo sensore

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  Serial.println("Lettura temperatura e umidità dal DHT22...");
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature(); // Celsius

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Errore nella lettura del sensore!");
    delay(2000);
    return;
  }

  Serial.print("Temperatura: ");
  Serial.print(temperature);
  Serial.print(" °C  |  Umidità: ");
  Serial.print(humidity);
  Serial.println(" %");

  delay(2000); // ogni 2 secondi
}
