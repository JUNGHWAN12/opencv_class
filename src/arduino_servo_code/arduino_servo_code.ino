#include <Servo.h>

// 팬(좌우) 서보 및 틸트(상하) 서보를 제어하기 위해 2개의 Servo 객체를 생성합니다.
Servo panServo;
Servo tiltServo;

// 아두이노 보드에 연결된 모터 디지털 신호 핀 (필요에 따라 변경 가능)
const int panPin = 9;   // Pan 제어를 맡는 모터가 연결된 핀
const int tiltPin = 10; // Tilt 제어를 맡는 모터가 연결된 핀

// 초기 제어 변수 (360도 Pan의 경우 90이 정지, 18 0도 Tilt의 경우 90이 중앙 각도)
int panSpeedAngle = 90;
int tiltAngle = 90;

void setup() {
  // 파이썬 측 Serial.Serial 통신 보드레이트와 동일하게 9600 으로 일치시켜 줍니다.
  Serial.begin(9600);
  
  // 지정 핀을 모터 활성화 핀으로 할당합니다.
  panServo.attach(panPin);
  tiltServo.attach(tiltPin);
  
  // 부팅 시 정지(Pan 90) 및 기준점 90도(Tilt)로 설정합니다.
  panServo.write(panSpeedAngle);
  tiltServo.write(tiltAngle);
}

void loop() {
  // 파이썬에서 넘어오는 데이터(예시: "P90T90\n")가 시리얼 버퍼에 도착했는지 확인합니다.
  if (Serial.available() > 0) {
    // 버퍼 내에 줄바꿈 문자('\n')를 만날 때까지 문자를 취합하여 String 으로 보관합니다.
    String data = Serial.readStringUntil('\n'); 
    
    // 포맷 문자 'P'와 'T'의 위치 값 인덱스를 파악합니다.
    int pIndex = data.indexOf('P');
    int tIndex = data.indexOf('T');
    
    // 정상 포맷으로 인식되었을 때 파싱 작업 진행
    if (pIndex != -1 && tIndex != -1) {
      
      // 'P' 다음부터 'T' 이전까지 문자를 슬라이싱해 정수로 캐스팅
      String panStr = data.substring(pIndex + 1, tIndex);
      // 'T' 다음부터 끝까지 문자를 슬라이싱해 정수로 캐스팅
      String tiltStr = data.substring(tIndex + 1);
      
      panSpeedAngle = panStr.toInt();
      tiltAngle = tiltStr.toInt();
      
      // 간혹 데이터 혼선으로 노이즈 값이 들어올 수 있으므로, 
      // constrain 함수를 통해 정상 신호 0~180 범위를 벗어날 때 잘라냅니다.
      panSpeedAngle = constrain(panSpeedAngle, 0, 180);
      tiltAngle = constrain(tiltAngle, 0, 180);
      
      // 추출된 신호 명령어를 모터에 전달하여 회전시킵니다.
      panServo.write(panSpeedAngle);
      tiltServo.write(tiltAngle);
    }
  }
}
