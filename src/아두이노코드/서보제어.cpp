#include <Servo.h>

Servo myServo;  // 서보모터 객체 생성

void setup() {
  Serial.begin(9600);   // 파이썬과 통신할 속도
  myServo.attach(9);    // 서보모터를 9번 핀에 연결
  myServo.write(0);     // 시작 위치 0도
}

void loop() {
  if (Serial.available() > 0) {
    char data = Serial.read();
    
    if (data == '1') {
      myServo.write(90);  // 사람 발견 시 90도
    } 
    else if (data == '0') {
      myServo.write(0);   // 사람 미발견 시 0도
    }
  }
}