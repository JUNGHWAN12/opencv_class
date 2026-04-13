import cv2
from ultralytics import YOLO

# ==========================================
# 1. 인공지능 모델 불러오기
# ==========================================
print("🧠 YOLO 모델을 불러오는 중입니다...")
# yolov8n.pt 모델을 다운로드하고 메모리에 올립니다. (최초 실행 시 다운로드 필요)
model = YOLO("yolov8n.pt") 

# ==========================================
# 2. 카메라 연결하기
# ==========================================
# 숫자 0은 컴퓨터에 연결된 기본 웹캠을 의미합니다.
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ 에러: 카메라를 열 수 없습니다.")
    exit()

print("✅ 카메라 연결 성공! (종료하려면 'q'를 누르세요)")

# ==========================================
# 3. 실시간 영상 처리 루프
# ==========================================
while True:
    # 카메라에서 사진(프레임)을 한 장씩 찍어옵니다.
    ret, frame = cap.read()
    if not ret:
        break
        
    # 거울처럼 보이도록 화면을 좌우 반전합니다. (선택 사항)
    frame = cv2.flip(frame, 1)

    # 🌟 AI에게 사진을 주고 객체를 찾으라고 명령합니다.
    # stream=True 옵션을 주면 실시간 영상에서 메모리를 덜 차지합니다.
    results = model.predict(frame, stream=True, verbose=False)
    
    # 🌟 찾은 결과(박스, 이름, 확률)를 원본 사진 위에 예쁘게 그립니다.
    for r in results:
        annotated_frame = r.plot() 
        
    # ==========================================
    # 4. 화면에 출력 및 종료 조건
    # ==========================================
    cv2.imshow("Step 1: Basic YOLO Detection", annotated_frame)

    # 1ms 동안 기다리며 키보드 입력을 확인합니다. 'q'를 누르면 종료!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 사용이 끝난 카메라와 창을 깔끔하게 정리합니다.
cap.release()
cv2.destroyAllWindows()
print("🛑 프로그램이 안전하게 종료되었습니다.")