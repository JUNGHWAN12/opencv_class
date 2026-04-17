import serial
import time

print("==================================================")
print(" 🎓 1교시: 파이썬(PySerial)으로 아두이노 LED 켜고 끄기 🎓 ")
print("==================================================")

# 1. 아두이노가 연결된 포트(컴퓨터의 USB 구멍 번호) 설정
port = 'COM4'  # 선생님/학생 컴퓨터에 맞게 COM 번호를 변경하세요!

try:
    # 2. 아두이노와 9600 속도로 통신 연결
    arduino = serial.Serial(port, 9600, timeout=1)
    
    # 통신선이 연결될 때까지 2초간 잠시 멈춰서 기다려줍니다. (매우 중요!)
    time.sleep(2) 
    print("✅ 아두이노 연결 성공! 통신을 시작합니다.\n")
except:
    print(f"❌ 아두이노 연결 실패! 장치 관리자에서 {port} 가 맞는지 확인하세요.")
    exit()

print("🌟 [학생들을 위한 미션] 🌟")
print("키보드 '1' + 엔터 ➡️ LED 켜기")
print("키보드 '0' + 엔터 ➡️ LED 끄기")
print("종료하려면 'q'를 누르세요.\n")

# 3. 우리가 'q'를 누를 때까지 무한 반복하며 명령을 받습니다.
while True:
    # 사용자가 키보드로 입력한 글자를 가져옵니다.
    user_input = input(">> 명령을 입력하세요 (1/0/q): ")
    
    if user_input == 'q':
        print("수업 코드를 종료합니다. 안녕!")
        break

    elif user_input == '1':
        arduino.write(b'1')  # 문자를 아두이노가 이해하는 바이트(b)로 바꿔서 전송!
        print("💡 반짝! 아두이노로 [켜짐] 신호를 보냈습니다.")

    elif user_input == '0':
        arduino.write(b'0')  
        print("🌑 소등! 아두이노로 [꺼짐] 신호를 보냈습니다.")

    else:
        print("🤔 잘못된 명령어입니다. 1, 0, q 중에서만 입력해주세요!")

# 4. 프로그램이 끝나면 아두이노와의 전화를 예의 바르게 끊어줍니다.
arduino.close()
