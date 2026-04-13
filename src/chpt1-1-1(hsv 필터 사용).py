import cv2
import numpy as np

# 트랙바 조작 시 호출될 빈 함수 (OpenCV 문법상 필요)
def empty(a):
    pass

# ==========================================
# 1. 조작 창(GUI) 생성 및 트랙바 부착
# ==========================================
cv2.namedWindow("HSV Adjuster")
cv2.resizeWindow("HSV Adjuster", 400, 300)

# H(색상: 0~179), S(채도: 0~255), V(명도: 0~255)
# 초기값은 모든 색상을 통과시키도록 (Min=0, Max=최대치) 설정해둡니다.
cv2.createTrackbar("Hue Min", "HSV Adjuster", 0, 179, empty)
cv2.createTrackbar("Hue Max", "HSV Adjuster", 179, 179, empty)
cv2.createTrackbar("Sat Min", "HSV Adjuster", 0, 255, empty)
cv2.createTrackbar("Sat Max", "HSV Adjuster", 255, 255, empty)
cv2.createTrackbar("Val Min", "HSV Adjuster", 0, 255, empty)
cv2.createTrackbar("Val Max", "HSV Adjuster", 255, 255, empty)

# 카메라 연결
cap = cv2.VideoCapture(0)

print("🎯 HSV 색상 추출기 가동! (종료: ESC)")
print("👉 마우스로 슬라이더를 움직여 원하는 물체만 하얗게 남겨보세요.")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # BGR -> HSV 변환
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # ==========================================
    # 2. 트랙바의 현재 슬라이더 값 실시간으로 읽어오기
    # ==========================================
    h_min = cv2.getTrackbarPos("Hue Min", "HSV Adjuster")
    h_max = cv2.getTrackbarPos("Hue Max", "HSV Adjuster")
    s_min = cv2.getTrackbarPos("Sat Min", "HSV Adjuster")
    s_max = cv2.getTrackbarPos("Sat Max", "HSV Adjuster")
    v_min = cv2.getTrackbarPos("Val Min", "HSV Adjuster")
    v_max = cv2.getTrackbarPos("Val Max", "HSV Adjuster")

    # 읽어온 값으로 배열 생성
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    # ==========================================
    # 3. 마스크 생성 및 원본 이미지와 합성
    # ==========================================
    mask = cv2.inRange(hsv, lower, upper)
    
    # 선택된 색상만 원래 색으로 보여주는 결과 화면 생성
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # 화면 상단에 현재 추출된 HSV 값을 글씨로 띄워주기 (복사하기 편하도록)
    text = f"Lower: [{h_min}, {s_min}, {v_min}]  Upper: [{h_max}, {s_max}, {v_max}]"
    cv2.putText(result, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # 3개의 창을 동시에 띄워서 비교하기
    cv2.imshow("1. Original", frame)
    cv2.imshow("2. Mask (B/W)", mask)
    cv2.imshow("3. Result (Color)", result)

    if cv2.waitKey(1) & 0xFF == 27: # ESC 키
        # 종료하기 직전에 터미널에도 값을 깔끔하게 출력해 줍니다.
        print("\n==================================")
        print("📋 복사해서 본 코드에 붙여넣으세요!")
        print(f"lower_color = np.array([{h_min}, {s_min}, {v_min}])")
        print(f"upper_color = np.array([{h_max}, {s_max}, {v_max}])")
        print("==================================\n")
        break

cap.release()
cv2.destroyAllWindows()