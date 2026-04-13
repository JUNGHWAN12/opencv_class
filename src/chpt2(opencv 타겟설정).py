import cv2
from ultralytics import YOLO

# ==========================================
# 1. 인공지능 모델 및 타겟(Target) 설정
# ==========================================
print("🧠 YOLO 모델 로드 중...")
model = YOLO("yolov8n.pt")

# 🌟 학생 미션: 어떤 물체만 잡을 것인가?
# COCO 데이터셋 기준: 0(사람), 67(휴대폰), 39(물병)
# 아래 리스트에 번호를 넣으면 AI가 그 물체만 쳐다봅니다!
TARGET_CLASSES = [0, 67] 

# ==========================================
# 2. 카메라 연결
# ==========================================
cap = cv2.VideoCapture(0)

# 화면 해상도를 640x480으로 고정 (연산 속도 확보)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("❌ 에러: 카메라를 열 수 없습니다.")
    exit()

print("✅ 2단계 추적 모드 가동! (종료: 'q')")

# ==========================================
# 3. 실시간 영상 분석 및 좌표 추출 루프
# ==========================================
while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # 🌟 필터링 적용: classes 옵션에 타겟 리스트를 넘겨줍니다.
    results = model.predict(frame, classes=TARGET_CLASSES, stream=True, verbose=False)
    
    # AI가 찾아낸 결과물들을 하나씩 뜯어봅니다.
    for r in results:
        boxes = r.boxes # 화면에 잡힌 모든 네모 박스들
        
        for box in boxes:
            # 1) 박스 모서리 좌표 가져오기 (x1, y1: 좌측 상단 / x2, y2: 우측 하단)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # 2) 물체 이름 알아내기
            cls = int(box.cls[0])
            name = model.names[cls]
            
            # ----------------------------------------
            # 🌟 3) 핵심 알고리즘: 중심점(X, Y) 계산하기 🌟
            # 가로의 절반(x1+x2)/2, 세로의 절반(y1+y2)/2 위치가 정중앙입니다.
            # ----------------------------------------
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            # 4) 화면에 시각적으로 표현하기
            # ① 타겟 테두리에 초록색 네모 그리기
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # ② 타겟 머리 위에 이름과 중심 좌표(X, Y) 글씨 쓰기
            text = f"{name} (X:{cx}, Y:{cy})"
            cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # ③ 정중앙에 빨간색 점 찍기 (반지름 5)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    # 최종 합성된 화면 출력
    cv2.imshow("Step 2: Smart Tracking Filter", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("🛑 2단계 프로그램 안전 종료")