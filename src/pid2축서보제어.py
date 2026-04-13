import cv2
import numpy as np
import serial
import time

# ==========================================
# 1. 초기 설정 (아두이노, 변수)
# ==========================================
port = 'COM3' # 포트 확인
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
except:
    print("❌ 아두이노 연결 실패")
    exit()

CENTER_X, CENTER_Y = 320, 240
pan_angle, tilt_angle = 90.0, 90.0

# 🌟 PID 게인 값 (이 값을 조절하는 것이 튜닝입니다)
Kp_x, Ki_x, Kd_x = 0.04, 0.001, 0.02
Kp_y, Ki_y, Kd_y = 0.04, 0.001, 0.02

# PID 계산을 위한 과거 데이터 저장용 변수
prev_error_x, prev_error_y = 0, 0
integral_x, integral_y = 0, 0
last_time = time.time()

# HSV 색상 범위 (초록색 예시)
lower_color = np.array([35, 100, 100])
upper_color = np.array([85, 255, 255])

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

print("🚀 2축 PID 추적 시스템 가동!")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 시간 계산 (dt)
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time

    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > 500:
            M = cv2.moments(c)
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            cv2.circle(frame, (cx, cy), 10, (0, 0, 255), -1)

            # 🌟 1. 오차 계산 (P)
            error_x = CENTER_X - cx
            error_y = CENTER_Y - cy

            if abs(error_x) > 20 or abs(error_y) > 20: # 데드존
                # 🌟 2. 적분 계산 (I) - 오차 누적
                integral_x += error_x * dt
                integral_y += error_y * dt
                
                # 안티 와인드업 (Anti-windup): I값이 무한정 커지는 것 방지
                integral_x = max(min(integral_x, 1000), -1000)
                integral_y = max(min(integral_y, 1000), -1000)

                # 🌟 3. 미분 계산 (D) - 오차의 변화 속도
                derivative_x = (error_x - prev_error_x) / dt if dt > 0 else 0
                derivative_y = (error_y - prev_error_y) / dt if dt > 0 else 0

                # 🌟 4. 최종 PID 출력 계산
                output_x = (Kp_x * error_x) + (Ki_x * integral_x) + (Kd_x * derivative_x)
                output_y = (Kp_y * error_y) + (Ki_y * integral_y) + (Kd_y * derivative_y)

                # 모터 각도에 적용 (방향이 반대면 += 대신 -= 사용)
                pan_angle -= output_x
                tilt_angle += output_y

                # 과거 오차 업데이트
                prev_error_x = error_x
                prev_error_y = error_y

            # 모터 한계치 고정
            pan_angle = max(10, min(170, pan_angle))
            tilt_angle = max(10, min(170, tilt_angle))

            # 아두이노로 전송
            command = f"X{int(pan_angle)}Y{int(tilt_angle)}\n"
            arduino.write(command.encode())
            
            cv2.putText(frame, f"PID X:{int(output_x)} Y:{int(output_y)}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    cv2.imshow("PID Tracker", frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
arduino.close()