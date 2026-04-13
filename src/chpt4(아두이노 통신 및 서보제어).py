import cv2
from ultralytics import YOLO
import serial
import time

# 1. 아두이노 연결 설정 (포트 번호 확인 필수!)
port = 'COM3' 
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2) # 아두이노 재부팅 대기
    print("✅ 아두이노와 연결되었습니다.")
except:
    print("❌ 아두이노 연결 실패! 포트 번호를 확인하세요.")
    exit()

# 2. YOLO 모델 로드
model = YOLO("yolov8n.pt")

# 3. 카메라 연결
cap = cv2.VideoCapture(0)

print("🚀 자율 추적 시스템 가동 중...")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # 🌟 사람(class 0)만 인식하도록 설정
    results = model.predict(frame, classes=[0], conf=0.5, verbose=False)
    
    person_detected = False
    
    for r in results:
        # 감지된 객체가 하나라도 있으면 True
        if len(r.boxes) > 0:
            person_detected = True
        
        # 화면에 박스 그리기
        annotated_frame = r.plot()

    # 4. 판단 및 명령 전송
    if person_detected:
        arduino.write(b'1') # 사람 있음 -> '1' 전송
        cv2.putText(annotated_frame, "STATUS: PERSON DETECTED", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    else:
        arduino.write(b'0') # 사람 없음 -> '0' 전송
        cv2.putText(annotated_frame, "STATUS: SEARCHING...", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("AI Human Tracking System", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()