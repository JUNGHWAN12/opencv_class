#include <Servo.h>

Servo panServo;  // 좌우(X축) 서보모터
Servo tiltServo; // 상하(Y축) 서보모터

// 초기 각도 설정 (정중앙)
int panAngle = 90;
int tiltAngle = 90;

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(10); // 통신 지연 시간을 줄여 반응 속도를 극대화합니다.
  
  panServo.attach(9);  // 좌우 모터는 9번 핀
  tiltServo.attach(10); // 상하 모터는 10번 핀
  
  panServo.write(panAngle);
  tiltServo.write(tiltAngle);
}

void loop() {
  // 파이썬으로부터 데이터가 들어오면
  if (Serial.available() > 0) {
    // 줄바꿈 문자('\n')가 나올 때까지 문자열을 읽습니다. (예: "X95Y120")
    String data = Serial.readStringUntil('\n'); 
    
    int x_pos = data.indexOf('X');
    int y_pos = data.indexOf('Y');
    
    // X와 Y가 모두 포함된 정상적인 데이터라면
    if (x_pos != -1 && y_pos != -1) {
      // 문자열을 잘라서 숫자로 변환합니다.
      panAngle = data.substring(x_pos + 1, y_pos).toInt();
      tiltAngle = data.substring(y_pos + 1).toInt();
      
      // 서보모터 각도 업데이트
      panServo.write(panAngle);
      tiltServo.write(tiltAngle);
    }
  }
}