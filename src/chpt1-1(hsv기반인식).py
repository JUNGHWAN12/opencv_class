import cv2
import numpy as np
import serial
import time

# ==========================================
# 1. 아두이노 연결 설정
# ==========================================
'''
port = 'COM3' # 💡 라즈베리파이에서 실행할 경우 '/dev/ttyACM0' 등으로 변경
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
    print("✅ 아두이노 연결 성공!")
except:
    print("❌ 연결 실패. 포트 번호나 시리얼 모니터를 확인하세요.")
    exit()
'''
# ==========================================
# 2. 추적할 색상(HSV) 범위 설정 (현재: 초록색 세팅)
# ==========================================
# H(색상), S(채도), V(명도)
lower_color = np.array([35, 100, 100])
upper_color = np.array([85, 255, 255])

cap = cv2.VideoCapture(0)
print("🚀 HSV 초경량 자율 추적 가동 중... (종료: ESC)")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # 1단계: BGR 이미지를 컴퓨터가 색을 구분하기 쉬운 HSV로 변환
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 2단계: 우리가 정한 색상만 하얀색(255), 나머지는 검은색(0)으로 칠하기 (마스크 생성)
    mask = cv2.inRange(hsv, lower_color, upper_color)

    # 3단계: 노이즈(자잘한 점) 제거를 위한 모폴로지 연산 (때 빼고 광내기)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # 4단계: 하얗게 칠해진 덩어리(윤곽선) 찾기
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    target_detected = False

    # 화면에 덩어리가 하나라도 있다면
    if len(contours) > 0:
        # 그중 가장 크기가 큰 덩어리를 타겟으로 지정
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        # 픽셀 500개 이상의 크기일 때만 진짜 타겟으로 인정 (노이즈 필터링)
        if area > 500:
            target_detected = True

            # 타겟의 중심점(cx, cy) 수학적으로 계산하기
            M = cv2.moments(c)
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # 원본 화면에 타겟 위치를 동그라미로 표시
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    # ==========================================
    # 3. 아두이노로 명령 전송
    # ==========================================
    if target_detected:
        #arduino.write(b'1')
        cv2.putText(frame, "TARGET FOUND!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        #arduino.write(b'0')
        cv2.putText(frame, "SEARCHING...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # 화면 2개 띄우기 (원본 화면 vs 컴퓨터가 보는 흑백 마스크 화면)
    cv2.imshow("Original Frame", frame)
    cv2.imshow("HSV Mask View", mask)

    if cv2.waitKey(1) & 0xFF == 27: # ESC 키
        break

cap.release()
cv2.destroyAllWindows()
# arduino.close()