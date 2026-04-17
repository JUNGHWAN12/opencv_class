import cv2
import serial
import time
import numpy as np

def empty(a):
    pass

# ==========================================
# 1. 아두이노 통신 및 시스템 초기화
# ==========================================
port = 'COM4' # 포트 번호 확인
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
    print("✅ 아두이노 연결 완료!")
except:
    print("❌ 아두이노 연결 실패!")
    exit()

# HSV 트랙바 생성 (색상 범위를 실시간으로 튜닝하기 위해)
cv2.namedWindow("Trackbars")
cv2.resizeWindow("Trackbars", 640, 240)
cv2.createTrackbar("Hue Min", "Trackbars", 0, 179, empty)
cv2.createTrackbar("Hue Max", "Trackbars", 179, 179, empty)
cv2.createTrackbar("Sat Min", "Trackbars", 100, 255, empty) # 기본값 (너무 흐린 색 제외)
cv2.createTrackbar("Sat Max", "Trackbars", 255, 255, empty)
cv2.createTrackbar("Val Min", "Trackbars", 100, 255, empty) # 기본값 (너무 어두운 색 제외)
cv2.createTrackbar("Val Max", "Trackbars", 255, 255, empty)

# Pan (360도 연속회전 모터) PID 제어 창
cv2.namedWindow("Pan PID (Left/Right)")
cv2.resizeWindow("Pan PID (Left/Right)", 400, 150)
cv2.createTrackbar("Kp (*1000)", "Pan PID (Left/Right)", 0, 200, empty)
cv2.createTrackbar("Ki (*1000)", "Pan PID (Left/Right)", 0, 50, empty)
cv2.createTrackbar("Kd (*1000)", "Pan PID (Left/Right)", 0, 200, empty)

# Tilt (180도 서보 모터) PID 제어 창
cv2.namedWindow("Tilt PID (Up/Down)")
cv2.resizeWindow("Tilt PID (Up/Down)", 400, 150)
cv2.createTrackbar("Kp (*1000)", "Tilt PID (Up/Down)", 0, 200, empty)
cv2.createTrackbar("Ki (*1000)", "Tilt PID (Up/Down)", 0, 50, empty)
cv2.createTrackbar("Kd (*1000)", "Tilt PID (Up/Down)", 0, 200, empty)

# ==========================================
# 2. PID 제어 변수 설정
# ==========================================
CENTER_X, CENTER_Y = 320, 240
pan_angle, tilt_angle = 90.0, 0

# PID 게인 (HSV 추적은 비교적 빠르므로 적절히 튜닝이 필요합니다)
Kp_x, Ki_x, Kd_x = 0, 0, 0
Kp_y, Ki_y, Kd_y = 0, 0, 0

prev_error_x, prev_error_y = 0, 0
integral_x, integral_y = 0, 0
last_time = time.time()

cap = cv2.VideoCapture(2,cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

print("🚀 HSV 색상 기반 자율 추적기 가동! (종료: ESC)")
print("👉 'Trackbars' 창에서 추적할 색상의 HSV 범위를 조절하세요.")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # ==========================================
    # 3. HSV 색상 변환 및 마스크 생성
    # ==========================================
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 트랙바에서 현재 HSV 범위 값 가져오기
    h_min = cv2.getTrackbarPos("Hue Min", "Trackbars")
    h_max = cv2.getTrackbarPos("Hue Max", "Trackbars")
    s_min = cv2.getTrackbarPos("Sat Min", "Trackbars")
    s_max = cv2.getTrackbarPos("Sat Max", "Trackbars")
    v_min = cv2.getTrackbarPos("Val Min", "Trackbars")
    v_max = cv2.getTrackbarPos("Val Max", "Trackbars")
    
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    
    # 해당 색상 범위에 참(255)인 마스크 이미지 생성
    mask = cv2.inRange(hsv, lower, upper)
    
    # 노이즈 제거 (모폴로지 연산 - 필요시 주석 해제)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 마스크 이미지에서 윤곽선(Contours) 찾기
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    
    target_found = False

    if len(contours) > 0:
        # 🌟 가장 큰 면적의 윤곽선 찾기 (가장 큰 객체만 추적)
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        
        # 노이즈 방지를 위해 일정 면적(500) 이상인 객체만 인식
        if area > 500:
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w // 2, y + h // 2
            
            target_found = True

            # 화면에 bounding box 및 중심점 표시
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, "TRACKING", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # ==========================================
            # 4. 실시간 추적을 위한 PID 연산 및 서보모터 제어
            # ==========================================
            # 트랙바에서 실시간으로 PID 상수를 가져와 적용합니다.
            scale = 1000.0
            Kp_x = cv2.getTrackbarPos("Kp (*1000)", "Pan PID (Left/Right)") / scale
            Ki_x = cv2.getTrackbarPos("Ki (*1000)", "Pan PID (Left/Right)") / scale
            Kd_x = cv2.getTrackbarPos("Kd (*1000)", "Pan PID (Left/Right)") / scale

            Kp_y = cv2.getTrackbarPos("Kp (*1000)", "Tilt PID (Up/Down)") / scale
            Ki_y = cv2.getTrackbarPos("Ki (*1000)", "Tilt PID (Up/Down)") / scale
            Kd_y = cv2.getTrackbarPos("Kd (*1000)", "Tilt PID (Up/Down)") / scale

            error_x = CENTER_X - cx
            error_y = CENTER_Y - cy

            # 360도 서보 모터(Pan)는 속도 제어입니다: 중앙 90을 기준으로 에러만큼 가감
            # 180도 서보 모터(Tilt)는 위치 제어입니다: 지난 각도에 에러만큼 계속 누적
            pan_speed = 90
            
            if abs(error_x) > 15: # 좌우 데드존 설정(미세한 떨림 방지)
                integral_x = max(min(integral_x + error_x * dt, 500), -500)
                derivative_x = (error_x - prev_error_x) / dt if dt > 0 else 0
                output_x = (Kp_x * error_x) + (Ki_x * integral_x) + (Kd_x * derivative_x)
                
                # 에러에 비례하여 90 기준 회전 속도 결정 (반대로 돈다면 90 + output_x 로 수정)
                pan_speed = 90 - output_x 
            else:
                integral_x = 0  # 멈출 때는 적분치 초기화
                
            if abs(error_y) > 15: # 상하 데드존 설정
                integral_y = max(min(integral_y + error_y * dt, 500), -500)
                derivative_y = (error_y - prev_error_y) / dt if dt > 0 else 0
                output_y = (Kp_y * error_y) + (Ki_y * integral_y) + (Kd_y * derivative_y)
                
                # 조립된 모터의 방향이 반대인 경우를 위해 기존 += 에서 -= 로 수정했습니다.
                tilt_angle -= output_y  # 180도 틸트는 위치 각도를 계속 누적
            else:
                integral_y = 0

            prev_error_x, prev_error_y = error_x, error_y

            # 출력 제한
            pan_speed = max(10, min(170, pan_speed))
            tilt_angle = max(10, min(170, tilt_angle))

            # 아두이노로 명령 전송 (아두이노 코드가 P와 T 문자를 기준으로 파싱합니다)
            command = f"P{int(pan_speed)}T{int(tilt_angle)}\n"
            arduino.write(command.encode())
            
            cv2.putText(frame, f"PAN_SPD: {int(pan_speed)} TILT: {int(tilt_angle)}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    if not target_found:
        # 360도 연속회전 모터의 경우 타겟을 놓쳤을 때 물리적으로 멈추도록 P90을 즉시 전송해야 합니다.
        command = f"P90T{int(tilt_angle)}\n"
        arduino.write(command.encode())
        
        cv2.putText(frame, "TARGET LOST!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        integral_x, integral_y = 0, 0 # 에러 누적 초기화 (안정성을 위함)
        prev_error_x, prev_error_y = 0, 0

    cv2.imshow("HSV Tracker", frame)
    cv2.imshow("Mask", mask) # 색상 필터링 결과를 보여주는 마스크 화면 함께 표시
    
    if cv2.waitKey(1) & 0xFF == 27: # ESC로 종료
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
