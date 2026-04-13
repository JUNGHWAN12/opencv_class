void setup() {
  // 파이썬과 통신할 속도(Baud Rate)를 9600으로 맞춥니다.
  Serial.begin(9600); 
  pinMode(13, OUTPUT); // 아두이노 보드의 내장 LED
}

void loop() {
  // 파이썬에서 보낸 데이터가 도착했는지 확인합니다.
  if (Serial.available() > 0) {
    // 도착한 데이터를 하나 읽어옵니다.
    char data = Serial.read(); 
    
    if (data == '1') {
      digitalWrite(13, HIGH); // LED 켜기
      Serial.println("Arduino: LED is ON!"); // 파이썬으로 확인 메시지 전송
    } 
    else if (data == '0') {
      digitalWrite(13, LOW);  // LED 끄기
      Serial.println("Arduino: LED is OFF!");
    }
  }
}