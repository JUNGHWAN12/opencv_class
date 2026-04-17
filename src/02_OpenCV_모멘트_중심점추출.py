import cv2
import numpy as np

# 1. 학생 컴퓨터에 달린 기본 카메라(또는 웹캠) 열기
cap = cv2.VideoCapture(2)

print("======================================================")
print(" 🎓 2교시: 모멘트(Moments) 수학으로 색상의 중심점 뚫어보기! 🎓 ")
print("======================================================")
print("파란색 물체를 카메라 앞에 대보세요!")

while True:
    # 2. 카메라에서 사진 한 장(프레임) 찍어서 가져오기
    ret, frame = cap.read()
    if not ret: break
    
    # 오른쪽/왼쪽 거울처럼 반전시켜주면 우리가 조종하기 더 편합니다.
    frame = cv2.flip(frame, 1) 

    # ----------------------------------------------------
    # 🔎 STEP 1. 컴퓨터가 보기 좋은 색상(HSV)으로 변환하기
    # ----------------------------------------------------
    # 기본 BGR(파,초,빨) 영상을 HSV(색,채도,밝기)로 바꿉니다. (사람 눈이 색을 구분하는 방식!)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 우리가 타올라라 찾고 싶은 파란색의 하한선과 상한선 지정
    lower_color = np.array([100, 150, 0])
    upper_color = np.array([140, 255, 255])
    
    # 이 색상 범위에 맞는 녀석만 '하얀색'으로, 나머지는 '검은색'으로 칠한 스케치북(마스크) 생성!
    mask = cv2.inRange(hsv, lower_color, upper_color)

    # ----------------------------------------------------
    # 🧹 STEP 2. 노이즈 제거 (모폴로지 연산)
    # ----------------------------------------------------
    kernel = np.ones((5,5), np.uint8) # 5x5 사이즈의 지우개/버터나이프 준비
    
    # 1차 작업 (MORPH_OPEN): 화면에 둥둥 떠다니는 픽셀 먼지들을 '지우개'로 싹싹 지워줍니다.
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 2차 작업 (MORPH_CLOSE): 물체 안에 파여있는 작은 빈틈(구멍)들을 '찰흙'으로 꾹꾹 메워줍니다.
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # ----------------------------------------------------
    # 🗺️ STEP 3. 윤곽선(Contour) 덩어리 찾기
    # ----------------------------------------------------
    # 하얗게 칠해진 스케치북(mask)에서 테두리 윤곽선들을 모두 찾습니다.
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 윤곽선 덩어리가 1개라도 발견되었다면 파헤쳐 봅시다!
    if len(contours) > 0:
        
        # 발견된 여러 빙산 조각들 중, '가장 면적이 큰 대장 덩어리' 하나만 골라냅니다.
        c = max(contours, key=cv2.contourArea)
        
        # 대장 덩어리의 '진짜 넓이(면적)'를 계산합니다.
        area = cv2.contourArea(c)
        
        # 먼지가 아니라 진짜 손이나 물체일 때만 인정해줍니다. (면적이 500픽셀 이상)
        if area > 500:
            
            # ----------------------------------------------------
            # 🎯 STEP 4. 모멘트(Moments) 수학을 이용한 무게중심 X,Y 추출
            # ----------------------------------------------------
            # 모멘트는 물리/수학에서 물체의 질량 중심을 구할 때 쓰는 공식입니다.
            M = cv2.moments(c)
            
            # M['m00']은 덩어리의 총 픽셀 개수(질량)을 뜻합니다. 분모가 0이 되면 치명적인 수학 에러가 뜨므로 안전장치를 걸어줍니다!
            if M['m00'] != 0:
                # 중심 X 좌표 = X의 총합(m10) / 총 질량(m00)
                cx = int(M['m10'] / M['m00'])  
                # 중심 Y 좌표 = Y의 총합(m01) / 총 질량(m00)
                cy = int(M['m01'] / M['m00'])  

                # 💡 시각화: 화면에 물체를 네모 박스로 감싸고 중심을 그려봅시다.
                x, y, w, h = cv2.boundingRect(c) # 물체를 둘러싸는 최소한의 직사각형 틀을 만듭니다.
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 물체 테두리에 초록색 박스 칠하기
                
                # 방금 우리가 수학으로 구해낸 무게중심(cx, cy) 위치에 빨간색 점(반지름 5) 찍기!
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                
                # 중심점 좌표(X, Y)를 영상 위에 글씨로 친절하게 띄워주기
                cv2.putText(frame, f"Center X:{cx} Y:{cy}", (cx - 40, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)


    # 학생들에게 실사 카메라 화면과 흑백 마스크 화면을 비교하며 보여줍니다.
    cv2.imshow("1. Original Camera", frame)
    cv2.imshow("2. Black & White Mask", mask)
    
    # 키보드 'ESC' 키를 누르면 종료!
    if cv2.waitKey(1) & 0xFF == 27:
        break

# 수업 끝! 카메라와 창들을 깔끔하게 치워줍니다.
cap.release()
cv2.destroyAllWindows()
