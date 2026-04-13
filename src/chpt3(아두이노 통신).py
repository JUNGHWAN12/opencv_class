import serial
import time

print("🔌 아두이노와 연결을 시도합니다...")

# 🌟 각자의 윈도우 장치관리자에서 확인한 COM 포트 번호로 변경해야 합니다!
# 통신 속도는 아두이노와 동일한 9600으로 맞춥니다.
port = 'COM3' 

try:
    # 아두이노와 시리얼 통신 연결
    arduino = serial.Serial(port, 9600, timeout=1)
    
    # 🌟 핵심 팁: 연결 직후 아두이노가 재부팅될 시간을 2초 정도 줘야 합니다.
    # 이 대기 시간이 없으면 첫 번째 명령이 무시됩니다.
    time.sleep(2)
    print("✅ 연결 성공!\n")

    # 1. 아두이노 켜기 명령 전송
    print("👉 파이썬: '1'을 보냅니다. (LED 켜기)")
    # 문자를 보낼 때는 반드시 byte 형식(b' ')으로 변환해서 보내야 합니다.
    arduino.write(b'1')
    time.sleep(0.5) # 아두이노가 처리할 시간을 잠깐 줍니다.
    
    # 아두이노가 잘 받았다고 보낸 메시지 읽어오기
    if arduino.readable():
        response = arduino.readline().decode().strip()
        print(f"👈 아두이노 대답: {response}\n")
        
    time.sleep(2) # 2초 대기

    # 2. 아두이노 끄기 명령 전송
    print("👉 파이썬: '0'을 보냅니다. (LED 끄기)")
    arduino.write(b'0')
    time.sleep(0.5)
    
    if arduino.readable():
        response = arduino.readline().decode().strip()
        print(f"👈 아두이노 대답: {response}\n")

    # 통신 종료
    arduino.close()
    print("🛑 통신이 안전하게 종료되었습니다.")

except serial.SerialException:
    print(f"❌ 에러: {port} 포트를 열 수 없습니다. 아두이노 시리얼 모니터 창이 켜져 있는지 확인하세요!")