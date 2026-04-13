import cv2
import numpy as np
import serial
import time

# ==========================================
# 1. 아두이노 연결
# ==========================================
port = 'COM3' # 본인의 포트 번호로 변경
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
    print("✅ 아두이노 연결 완료!")
except:
    print("❌ 아두이노 연결 실패!")
    exit()

# ==========================================
# 2. 제어 변수 및 PID 상수 설정
# ==========================================
CENTER_X = 320  # 화면 가로 중앙 (640 / 2)
CENTER_Y = 240  # 화면 세로 중앙 (480 / 2)

pan_angle = 90.0  # 좌우 모터 초기 각도
tilt_angle = 90.0 # 상하 모터 초기 각도

# 🌟 감도(Kp) 설정: 모터가 너무 휙휙 돌면 이 값을 줄이고, 너무 느리면 올리세요.
Kp_pan = 0.05  
Kp_tilt = 0.05 

# 추적할 색상 범위 (앞서 구한 값으로 변경하세요. 현재는 임의의 초록색)
lower_color = np.array([35, 100, 100])
upper_color = np.array([85, 255, 255])

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("🚀 2축 자율 추적 시스템 가동! (종료: ESC)")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1) # 거울 모드

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > 500: # 노이즈 필터링
            M = cv2.moments(c)
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # 원본 화면에 타겟 표시
            cv2.circle(frame, (cx, cy), 10, (0, 0, 255), -1)

            # ==========================================
            # 3. 2축 오차 계산 및 모터 각도 보정
            # ==========================================
            error_x = CENTER_X - cx
            error_y = CENTER_Y - cy

            # 🌟 데드존(Deadzone) 설정: 중심 근처(오차 30픽셀 이내)면 모터를 정지시켜 진동(지터링) 방지
            if abs(error_x) > 30:
                pan_angle -= error_x * Kp_pan
            if abs(error_y) > 30:
                tilt_angle += error_y * Kp_tilt # 방향이 반대면 부호를 -로 변경하세요

            # SG-90 모터의 물리적 한계 방어 (0도 ~ 180도)
            pan_angle = max(10, min(170, pan_angle))
            tilt_angle = max(10, min(170, tilt_angle))

            # ==========================================
            # 4. 아두이노로 좌표 전송
            # ==========================================
            # 예: "X95Y120\n" 형태로 문자열 조립 후 전송
            command = f"X{int(pan_angle)}Y{int(tilt_angle)}\n"
            arduino.write(command.encode())
            
            # 화면에 현재 각도 표시
            cv2.putText(frame, f"PAN: {int(pan_angle)} TILT: {int(tilt_angle)}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # 화면 중앙 십자선 그리기
    cv2.line(frame, (CENTER_X, 0), (CENTER_X, 480), (255, 0, 0), 1)
    cv2.line(frame, (0, CENTER_Y), (640, CENTER_Y), (255, 0, 0), 1)

    cv2.imshow("2-Axis HSV Tracker", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()