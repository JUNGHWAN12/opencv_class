import cv2
import serial
import time
from ultralytics import YOLO

def empty(a): pass

# ==========================================
# 1. 아두이노 통신 및 시스템 초기화
# ==========================================
port = 'COM4' 
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
    print("✅ 아두이노 연결 완료!")
except:
    print("❌ 아두이노 연결 실패! 포트(COM번)를 확인하세요.")
    exit()

# ==========================================
# 2. YOLO OpenVINO 초고속 모델 로드
# ==========================================
print("🧠 인텔 전용 초고속 OpenVINO 가속 엔진 로드 중...")
# .pt 파일이 아니라 _openvino_model 경로(폴더)를 지정합니다!
model = YOLO("d:/opencv_class/yolo26n_openvino_model/")

# ==========================================
# 3. 설정 창 (클래스 선택 및 개별 PID 제어)
# ==========================================
# 추적할 클래스 선택 창
cv2.namedWindow("Tracking Settings")
cv2.resizeWindow("Tracking Settings", 400, 100)
# 클래스: COCO 데이터셋 기준 0~79 (0: 사람, 39: 병 등), 80이면 '모두 추적'
cv2.createTrackbar("Class (80=ALL)", "Tracking Settings", 0, 80, empty)

# Pan (360도 연속회전 모터) PID 제어 창
cv2.namedWindow("Pan PID (Left/Right)")
cv2.resizeWindow("Pan PID (Left/Right)", 400, 150)
cv2.createTrackbar("Kp (*1000)", "Pan PID (Left/Right)", 100, 200, empty)
cv2.createTrackbar("Ki (*1000)", "Pan PID (Left/Right)", 1, 50, empty)
cv2.createTrackbar("Kd (*1000)", "Pan PID (Left/Right)", 10, 200, empty)

# Tilt (180도 서보 모터) PID 제어 창
cv2.namedWindow("Tilt PID (Up/Down)")
cv2.resizeWindow("Tilt PID (Up/Down)", 400, 150)
cv2.createTrackbar("Kp (*1000)", "Tilt PID (Up/Down)", 20, 200, empty)
cv2.createTrackbar("Ki (*1000)", "Tilt PID (Up/Down)", 1, 50, empty)
cv2.createTrackbar("Kd (*1000)", "Tilt PID (Up/Down)", 10, 200, empty)

# ==========================================
# 4. 카메라 및 PID 초기 변수 설정
# ==========================================
CENTER_X, CENTER_Y = 320, 240
pan_speed, tilt_angle = 90.0, 0.0

prev_error_x, prev_error_y = 0, 0
integral_x, integral_y = 0, 0
last_time = time.time()

camera_index = 2
cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

if not cap.isOpened():
    print(f"❌ {camera_index}번 카메라를 열 수 없습니다!")
    exit()

print("🚀 인텔 OpenVINO 초고속 자율 추적 가동! (종료: ESC)")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time

    # ==========================================
    # 실시간 설정 값 읽기
    # ==========================================
    target_class = cv2.getTrackbarPos("Class (80=ALL)", "Tracking Settings")
    
    scale = 1000.0
    Kp_x = cv2.getTrackbarPos("Kp (*1000)", "Pan PID (Left/Right)") / scale
    Ki_x = cv2.getTrackbarPos("Ki (*1000)", "Pan PID (Left/Right)") / scale
    Kd_x = cv2.getTrackbarPos("Kd (*1000)", "Pan PID (Left/Right)") / scale

    Kp_y = cv2.getTrackbarPos("Kp (*1000)", "Tilt PID (Up/Down)") / scale
    Ki_y = cv2.getTrackbarPos("Ki (*1000)", "Tilt PID (Up/Down)") / scale
    Kd_y = cv2.getTrackbarPos("Kd (*1000)", "Tilt PID (Up/Down)") / scale

    # ==========================================
    # YOLO 추론 (OpenVINO 가속)
    # ==========================================
    # 이미 320포맷으로 변환된 폴더이므로 엄청난 속도로 실행됩니다!
    if target_class == 80:
        results = model.predict(frame, verbose=False)
    else:
        results = model.predict(frame, classes=[target_class], verbose=False)

    largest_area = 0
    best_target = None
    best_class_name = ""

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = (x2 - x1) * (y2 - y1)
            if area > largest_area:
                largest_area = area
                best_target = (x1, y1, x2, y2)
                cls_id = int(box.cls[0])
                best_class_name = model.names[cls_id]

    if best_target is not None:
        x1, y1, x2, y2 = best_target
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

        # 타겟 시각화
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(frame, f"TARGET: {best_class_name}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # PID 연산
        error_x = CENTER_X - cx
        error_y = CENTER_Y - cy

        if abs(error_x) > 15:
            integral_x = max(min(integral_x + error_x * dt, 500), -500)
            derivative_x = (error_x - prev_error_x) / dt if dt > 0 else 0
            output_x = (Kp_x * error_x) + (Ki_x * integral_x) + (Kd_x * derivative_x)
            pan_speed = 90 - output_x
        else:
            integral_x = 0  
            pan_speed = 90

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
        
        cv2.putText(frame, f"PAN: {int(pan_speed)} TILT: {int(tilt_angle)}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    else:
        command = f"P90T{int(tilt_angle)}\n" 
        arduino.write(command.encode())
        mode_text = "ALL CLASSES" if target_class == 80 else f"CLASS: {target_class}"
        cv2.putText(frame, f"SEARCHING... [{mode_text}]", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        integral_x, integral_y = 0, 0 
        prev_error_x, prev_error_y = 0, 0

    cv2.imshow("OpenVINO Intel GPU Tracker", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
try: arduino.close()
except: pass
