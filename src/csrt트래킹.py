import cv2
import serial
import time

def empty(a): pass

# ============ 1. 실시간 마우스 드래그 추적 시스템 ============
drawing = False
ix, iy = -1, -1
temp_bbox = None
bbox_to_init = None
tracking_started = False
tracker = None
tracker_name = "KCF"

def mouse_callback(event, x, y, flags, param):
    global ix, iy, drawing, temp_bbox, bbox_to_init, tracking_started
    if not tracking_started:
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy = x, y
            temp_bbox = (ix, iy, 0, 0)
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                # 사용자가 드래그하는 동안 실시간으로 영역 시각화
                temp_bbox = (min(ix, x), min(iy, y), abs(x - ix), abs(y - iy))
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            w = abs(x - ix)
            h = abs(y - iy)
            temp_bbox = None
            if w > 10 and h > 10:
                # 마우스 클릭을 떼는 순간, 그 위치를 타겟으로 예약
                bbox_to_init = (min(ix, x), min(iy, y), w, h)

# ==========================================
# 2. 아두이노 통신 및 시스템 초기화
# ==========================================
port = 'COM4' 
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
    print("✅ 아두이노 연결 완료!")
except:
    print("❌ 아두이노 연결 실패!")
    exit()

# 화면 콜백 부착
cv2.namedWindow("Object Tracker")
cv2.setMouseCallback("Object Tracker", mouse_callback)

# PID 실시간 제어 트랙바
cv2.namedWindow("PID Tuning")
cv2.resizeWindow("PID Tuning", 400, 150)
cv2.createTrackbar("Kp (*1000)", "PID Tuning", 40, 200, empty)
cv2.createTrackbar("Ki (*1000)", "PID Tuning", 1, 50, empty)
cv2.createTrackbar("Kd (*1000)", "PID Tuning", 20, 200, empty)

CENTER_X, CENTER_Y = 320, 240
pan_angle, tilt_angle = 90.0, 90.0
prev_error_x, prev_error_y = 0, 0
integral_x, integral_y = 0, 0
last_time = time.time()

camera_index = 2
cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

print("🚀 KCF 최고속 자율 추적기 가동! (종료: ESC)")
print("👉 영상이 멈추지 않습니다! 작동 중인 화면 위에 직접 마우스를 드래그하여 물체를 잡아보세요!")

# ==========================================
# 3. 메인 루프 (버퍼 멈춤 없는 완전 실시간)
# ==========================================
while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # 사용자가 마우스로 드래그 중인 박스 그리기
    if temp_bbox is not None and not tracking_started:
        tx, ty, tw, th = temp_bbox
        cv2.rectangle(frame, (tx, ty), (tx + tw, ty + th), (255, 255, 0), 2)

    # 마우스를 뗀 순간 추적기 즉시 초기화
    if bbox_to_init is not None:
        try:
            tracker = cv2.TrackerKCF_create()
            tracker_name = "KCF"
        except AttributeError:
            tracker = cv2.TrackerMIL_create()
            tracker_name = "MIL"
            
        tracker.init(frame, bbox_to_init)
        tracking_started = True
        bbox_to_init = None # 초기화 후 예약 비우기
        last_time = time.time()
        print(f"🎯 타겟 락온 완료! {tracker_name} 실시간 추적을 시작합니다.")

    # 추적 지정 전 대기 화면
    if not tracking_started:
        cv2.putText(frame, "Live: Drag mouse to select target", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    # 진짜 실시간 추적 루프
    else:
        success, bbox = tracker.update(frame)
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        if success:
            x, y, w, h = [int(v) for v in bbox]
            cx, cy = x + w // 2, y + h // 2

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, "TRACKING", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            scale = 1000.0
            kp_val = cv2.getTrackbarPos("Kp (*1000)", "PID Tuning") / scale
            ki_val = cv2.getTrackbarPos("Ki (*1000)", "PID Tuning") / scale
            kd_val = cv2.getTrackbarPos("Kd (*1000)", "PID Tuning") / scale
            
            Kp_x, Ki_x, Kd_x = kp_val, ki_val, kd_val
            Kp_y, Ki_y, Kd_y = kp_val, ki_val, kd_val

            error_x = CENTER_X - cx
            error_y = CENTER_Y - cy

            pan_speed = 90
            if abs(error_x) > 15:
                integral_x = max(min(integral_x + error_x * dt, 500), -500)
                derivative_x = (error_x - prev_error_x) / dt if dt > 0 else 0
                output_x = (Kp_x * error_x) + (Ki_x * integral_x) + (Kd_x * derivative_x)
                pan_speed = 90 - output_x 
            else:
                integral_x = 0  
                
            if abs(error_y) > 15:
                integral_y = max(min(integral_y + error_y * dt, 500), -500)
                derivative_y = (error_y - prev_error_y) / dt if dt > 0 else 0
                output_y = (Kp_y * error_y) + (Ki_y * integral_y) + (Kd_y * derivative_y)
                tilt_angle -= output_y
            else:
                integral_y = 0

            prev_error_x, prev_error_y = error_x, error_y

            pan_speed = max(10, min(170, pan_speed))
            tilt_angle = max(10, min(170, tilt_angle))

            command = f"P{int(pan_speed)}T{int(tilt_angle)}\n"
            arduino.write(command.encode())
            
            cv2.putText(frame, f"PAN_SPD: {int(pan_speed)} TILT: {int(tilt_angle)}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        else: # 추적 실패 시 (타겟 이탈, 일시적 가려짐 등)
            command = f"P90T{int(tilt_angle)}\n"
            arduino.write(command.encode())
            
            # 초기화하지 않고 기다림 (완전 수동 초기화는 키보드 'c' 사용)
            cv2.putText(frame, "TARGET LOST! WAITING... (Press 'c' to Reset)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            integral_x, integral_y = 0, 0 
            prev_error_x, prev_error_y = 0, 0
            # tracking_started = False # 강제 초기화 방지

    cv2.imshow("Object Tracker", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == 27: # ESC로 종료
        break
    elif key == ord('c'): # 스페이스바 오류 등을 대비해 c를 누르면 강제 수동 초기화
        tracking_started = False
        command = f"P90T{int(tilt_angle)}\n"
        try: arduino.write(command.encode())
        except: pass

cap.release()
cv2.destroyAllWindows()
try: arduino.close()
except: pass