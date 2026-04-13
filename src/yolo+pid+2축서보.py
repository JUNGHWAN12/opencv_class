import cv2
import serial
import time
from ultralytics import YOLO

# ==========================================
# 1. 시스템 초기화 및 통신 설정
# ==========================================
port = 'COM3' # 아두이노 포트 확인
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
    print("✅ 아두이노(신경망) 연결 완료!")
except:
    print("❌ 연결 실패. 포트 번호를 확인하세요.")
    exit()

# 🌟 AI 뇌 탑재 (학생들이 직접 학습시킨 best.pt를 넣어도 됩니다!)
print("🧠 YOLO 모델 로드 중...")
model = YOLO("yolov8n.pt") 
TARGET_CLASS = 0 # 0: 사람 (추적할 타겟)

# ==========================================
# 2. 제어 컨트롤러 (PID) 설정
# ==========================================
CENTER_X, CENTER_Y = 320, 240
pan_angle, tilt_angle = 90.0, 90.0

# 🌟 PID 게인: YOLO는 연산이 무거워 프레임이 낮으므로, HSV때보다 P값을 살짝 낮추는 것이 좋습니다.
Kp_x, Ki_x, Kd_x = 0.03, 0.001, 0.015
Kp_y, Ki_y, Kd_y = 0.03, 0.001, 0.015

prev_error_x, prev_error_y = 0, 0
integral_x, integral_y = 0, 0
last_time = time.time()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

print("🚀 최종: AI x PID 자율 추적 시스템 가동! (종료: ESC)")

# ==========================================
# 3. 실시간 AI 분석 및 PID 제어 루프
# ==========================================
while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # YOLO AI 추론
    results = model.predict(frame, classes=[TARGET_CLASS], verbose=False)
    
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time

    largest_area = 0
    best_target = None

    # 여러 객체 중 가장 큰(가까운) 타겟 하나만 고르기 🌟
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = (x2 - x1) * (y2 - y1)
            if area > largest_area:
                largest_area = area
                best_target = (x1, y1, x2, y2)

    if best_target is not None:
        x1, y1, x2, y2 = best_target
        
        # 타겟의 중심점(cx, cy) 계산
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        # 화면에 타겟 표시
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(frame, "TARGET LOCKED", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # ==========================================
        # 4. PID 연산 및 모터 구동
        # ==========================================
        error_x = CENTER_X - cx
        error_y = CENTER_Y - cy

        if abs(error_x) > 20 or abs(error_y) > 20: # 데드존
            integral_x = max(min(integral_x + error_x * dt, 500), -500)
            integral_y = max(min(integral_y + error_y * dt, 500), -500)

            derivative_x = (error_x - prev_error_x) / dt if dt > 0 else 0
            derivative_y = (error_y - prev_error_y) / dt if dt > 0 else 0

            output_x = (Kp_x * error_x) + (Ki_x * integral_x) + (Kd_x * derivative_x)
            output_y = (Kp_y * error_y) + (Ki_y * integral_y) + (Kd_y * derivative_y)

            pan_angle -= output_x
            tilt_angle += output_y

            prev_error_x, prev_error_y = error_x, error_y

        # 모터 각도 제한 및 전송
        pan_angle = max(10, min(170, pan_angle))
        tilt_angle = max(10, min(170, tilt_angle))

        command = f"X{int(pan_angle)}Y{int(tilt_angle)}\n"
        arduino.write(command.encode())
        
        cv2.putText(frame, f"PAN: {int(pan_angle)} TILT: {int(tilt_angle)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    else:
        # 타겟을 잃어버렸을 때의 상태 표시
        cv2.putText(frame, "SEARCHING...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Final: AI x PID Tracking System", frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
arduino.close()