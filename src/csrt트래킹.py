import cv2
import serial
import time

# ==========================================
# 1. 아두이노 통신 및 시스템 초기화
# ==========================================
port = 'COM3' # 포트 번호 확인
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
    print("✅ 아두이노 연결 완료!")
except:
    print("❌ 아두이노 연결 실패!")
    exit()

# 🌟 CSRT 추적기 생성
tracker = cv2.TrackerCSRT_create()
tracking_started = False # 추적 시작 여부를 확인하는 깃발(Flag)

# ==========================================
# 2. PID 제어 변수 설정
# ==========================================
CENTER_X, CENTER_Y = 320, 240
pan_angle, tilt_angle = 90.0, 90.0

# PID 게인 (CSRT는 프레임 속도가 일정하므로 튜닝하기가 좋습니다)
Kp_x, Ki_x, Kd_x = 0.04, 0.001, 0.02
Kp_y, Ki_y, Kd_y = 0.04, 0.001, 0.02

prev_error_x, prev_error_y = 0, 0
integral_x, integral_y = 0, 0
last_time = time.time()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

print("🚀 CSRT 기반 자율 추적기 가동! (종료: ESC)")
print("👉 화면에서 타겟이 보이면 키보드 's'를 누르세요!")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # ==========================================
    # 3. 목표물 수동 지정 모드 (키보드 's' 입력 시)
    # ==========================================
    if not tracking_started:
        cv2.putText(frame, "Press 's' to select target", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("CSRT Tracker", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # 🌟 마우스로 추적할 영역(ROI)을 그리는 창을 띄웁니다.
            # 드래그 후 SPACE 또는 ENTER 키를 누르면 확정됩니다.
            bbox = cv2.selectROI("CSRT Tracker", frame, fromCenter=False, showCrosshair=True)
            
            # 제대로 박스를 그렸다면 추적기 초기화
            if bbox[2] > 0 and bbox[3] > 0: 
                tracker.init(frame, bbox)
                tracking_started = True
                print("🎯 타겟 락온 완료! 추적을 시작합니다.")
        elif key == 27: # ESC
            break
        continue

    # ==========================================
    # 4. 실시간 추적 및 PID 제어 루프
    # ==========================================
    # 추적기 업데이트 (현재 화면에서 아까 그 패턴이 어디 있는지 찾기)
    success, bbox = tracker.update(frame)
    
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time

    if success:
        # 박스 좌표 추출 (x, y, 가로길이, 세로길이)
        x, y, w, h = [int(v) for v in bbox]
        cx, cy = x + w // 2, y + h // 2

        # 화면에 표시
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(frame, "TRACKING", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # PID 연산
        error_x = CENTER_X - cx
        error_y = CENTER_Y - cy

        if abs(error_x) > 15 or abs(error_y) > 15: # 데드존 설정
            integral_x = max(min(integral_x + error_x * dt, 500), -500)
            integral_y = max(min(integral_y + error_y * dt, 500), -500)

            derivative_x = (error_x - prev_error_x) / dt if dt > 0 else 0
            derivative_y = (error_y - prev_error_y) / dt if dt > 0 else 0

            output_x = (Kp_x * error_x) + (Ki_x * integral_x) + (Kd_x * derivative_x)
            output_y = (Kp_y * error_y) + (Ki_y * integral_y) + (Kd_y * derivative_y)

            pan_angle -= output_x
            tilt_angle += output_y

            prev_error_x, prev_error_y = error_x, error_y

        pan_angle = max(10, min(170, pan_angle))
        tilt_angle = max(10, min(170, tilt_angle))

        command = f"X{int(pan_angle)}Y{int(tilt_angle)}\n"
        arduino.write(command.encode())
        
        cv2.putText(frame, f"PAN: {int(pan_angle)} TILT: {int(tilt_angle)}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    else:
        # 추적 실패 시 (물체가 화면 밖으로 나감)
        cv2.putText(frame, "TARGET LOST!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        tracking_started = False # 다시 선택 모드로 돌아감

    cv2.imshow("CSRT Tracker", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()