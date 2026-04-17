import cv2
import serial
import time
import numpy as np

print("===================================================================")
print(" 🎓 6교시: 서보모터(SG-90) 제어 기초 - 키보드로 팬틸트 조종하기! 🎓 ")
print("===================================================================")

port = 'COM4'
try:
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)
    print("✅ 아두이노 연결 성공! 로봇 팔(팬틸트)과 통신을 시작합니다.")
except:
    print(f"❌ 아두이노 연결 실패! 장치 관리자에서 {port} 가 맞는지 확인하세요.")
    exit()

# [Pan 모터는 360도 무한회전 모터입니다!] 
# 90은 '정지 속도'를 의미합니다. (0~89, 91~180 은 속도와 방향을 의미함)
pan_speed = 90
# [Tilt 모터는 180도 각도 모터입니다!]
tilt_angle = 0

# 키보드 입력을 받기 위해 까만 도화지(창)를 하나 만듭니다.
bg = np.zeros((300, 600, 3), dtype=np.uint8)

print("\n🌟 [조작 방법] 🌟")
print("반드시 새로 뜬 까만 화면에 마우스를 클릭해 둔 상태에서 키보드를 누르세요!")
print("방향키 'A' / 'D' : Pan 모터 (좌우 속도 제어, 누를수록 빨라짐!)")
print("⚡ 스페이스바(SPACE) : Pan 모터 급정지 (90번 속도)")
print("방향키 'W' / 'S' : Tilt 모터 (상하 각도 조절)")
print("그만하려면 'ESC' 키를 누르세요.\n")

while True:
    # 1. 시각화: 현재 모터의 각도가 몇 도인지 화면에 예쁘게 그려줍니다.
    display = bg.copy()
    cv2.putText(display, f"Pan Speed (A/D): {pan_speed}", (50, 100), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 200, 0), 2)
    cv2.putText(display, f"Tilt Angle (W/S): {tilt_angle}", (50, 200), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 200), 2)
    
    cv2.imshow("6th Lesson: Keyboard Servo Controller", display)

    # 2. 키보드 입력 받기 (cv2.waitKey)
    key = cv2.waitKey(10) & 0xFF
    
    # 3. 키보드 조작에 따른 각도/속도 제어
    if key == 27: # ESC 키
        print("수업 코드를 종료합니다.")
        break
    
    # [Pan 360도 스피드 제어]
    # 모터 내부의 뻑뻑함(데드밴드)을 곧바로 이겨내기 위해 한 번에 20 단위로 강하게 속도를 줍니다!
    elif key == ord('a'):
        pan_speed = max(0, pan_speed - 20)  # 90 -> 70 -> 50 (왼쪽으로 강하게!)
    elif key == ord('d'):
        pan_speed = min(180, pan_speed + 20) # 90 -> 110 -> 130 (오른쪽으로 강하게!)
    elif key == ord(' '): # 스페이스바
        pan_speed = 90 # 즉시 정지 상태로!
        print("🛑 급정지!")
        
    # [Tilt 180도 각도 제어]
    elif key == ord('w'):
        tilt_angle = max(0, tilt_angle - 5)
    elif key == ord('s'):
        tilt_angle = min(180, tilt_angle + 5)
    
    # 4. 아두이노로 명령어 문자열 전송하기 
    command = f"P{pan_speed}T{tilt_angle}\n"
    arduino.write(command.encode())

arduino.close()
cv2.destroyAllWindows()
