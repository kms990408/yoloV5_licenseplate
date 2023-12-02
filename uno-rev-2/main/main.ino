#include <Wire.h>
#include <Firebase_Arduino_WiFiNINA.h>
#include <NewPing.h>
#include<Servo.h>

// Firebase 설정
#define FIREBASE_HOST "license-d68c6-default-rtdb.firebaseio.com"
#define FIREBASE_AUTH "qyQJdDEJv7Kn61As6rjle22QmTzViiHIGoGLC0ba"

// WiFi 설정
#define SSID "U+Net7120"
#define SSID_PASSWORD "DD9B003487"
// Firebase 키 설정
#define PARKING_SPOT_STATE_KEY "/parking_spot_state"
#define A1 "A1"
#define A2 "A2"

// 핀 번호 설정
#define A1_TRIG_PIN 2
#define A1_ECHO_PIN 3
#define A2_TRIG_PIN 4
#define A2_ECHO_PIN 5

int count1=0;
int count2=0;

NewPing a1Sensor(A1_TRIG_PIN, A1_ECHO_PIN);
NewPing a2Sensor(A2_TRIG_PIN, A2_ECHO_PIN);

// 센서 구조체 정의
struct Sensor {
  const int trigPin;
  const int echoPin;
  bool state;
};

// A1, A2 센서 설정
Sensor a1SensorStruct = { A1_TRIG_PIN, A1_ECHO_PIN, false };
Sensor a2SensorStruct = { A2_TRIG_PIN, A2_ECHO_PIN, false };

FirebaseData firebaseData;
Servo myservo;

// 시간 변수 추가
unsigned long last = 0;

String path1 = String(PARKING_SPOT_STATE_KEY) + "/" + "A1";
String path2 = String(PARKING_SPOT_STATE_KEY) + "/" + "A2";

// 초기 설정 함수
void setup() {
  Serial.begin(9600);  // 보정된 통신 속도
  myservo.attach(12);

  // WiFi 연결
  WiFi.begin(SSID, SSID_PASSWORD);
  Serial.print("Wi-Fi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.print("\nWi-Fi connected - IP address: ");
  Serial.println(WiFi.localIP());
  delay(500);

  // Firebase 초기화
  Firebase.begin(FIREBASE_HOST, FIREBASE_AUTH, SSID, SSID_PASSWORD);
}

// 주차 공간 상태 Firebase 업데이트 함수
void publish_parking_spot_state(char* parking_spot_name, bool state) {
  String path = String(PARKING_SPOT_STATE_KEY) + "/" + String(parking_spot_name);
  return Firebase.setBool(firebaseData, path.c_str(), state);
}

// 루프 함수
void loop() {

  // 일정 주기로 센서 상태 업데이트
  if (millis() > last + 3000) {
    last = millis();

    int distanceA1 = a1Sensor.ping_cm();  // 거리 측정
    int distanceA2 = a2Sensor.ping_cm();

    // A1 주차 공간 상태 업데이트
    if (distanceA1 < 10 && !a1SensorStruct.state) {
      if(count1==0){
      myservo.write(0);
      a1SensorStruct.state = true;
      Firebase.setBool(firebaseData, path1.c_str(), true);
      count1 = 1;
      delay(10000);}
    }
    if (distanceA1 >= 10 && a1SensorStruct.state) {
      a1SensorStruct.state = false;
      Firebase.setBool(firebaseData, path1.c_str(), false);
      count1 = 0;
    }
    // Serial Monitor

    Serial.print("Setting state for A1 to ");
    Serial.println(a1SensorStruct.state ? "true" : "false");

    Serial.print("Distance: ");
    Serial.println(distanceA1);

    // A2 주차 공간 상태 업데이트
    if (distanceA2 < 10 && !a2SensorStruct.state) {
      if(count2 == 0){
      myservo.write(180);
      a2SensorStruct.state = true;
      Firebase.setBool(firebaseData, path2.c_str(), true);
      count2 = 1;}
    }
    if (distanceA2 >= 10 && a2SensorStruct.state) {
      a2SensorStruct.state = false;
      Firebase.setBool(firebaseData, path2.c_str(), false);
      count2 = 0;
    }

    // Serial Monitor
    
    Serial.print("Setting state for A2 to ");
    Serial.println(a2SensorStruct.state ? "true" : "false");

    Serial.print("Distance: ");
    Serial.println(distanceA2);
  }
}
