from ultralytics import YOLO
import sys

print("==============================================")
print("  🚀 인텔 내장 그래픽(OpenVINO) 초고속 변환기  ")
print("==============================================")

# 1. 변환할 모델 경로 설정 (가위바위보를 하고 싶다면 가위바위보.pt 로 바꾸시면 됩니다!)
model_path = "d:/opencv_class/yolo26n.pt"

print(f"\n[{model_path}] 모델을 불러옵니다...")
model = YOLO(model_path)

print("\n⚙️ 인텔 GPU(Iris Xe)전용 포맷으로 압축/변환을 시작합니다.")
print("  (컴퓨터의 성능에 따라 1~5분 정도 소요될 수 있습니다. 끄지 말고 기다려주세요!)")

# 2. OpenVINO 포맷으로 압축 변환
# imgsz=320 고정 연산으로 압축하면 속도가 최대로 나옵니다.
model.export(format="openvino", imgsz=640)

print("\n✅ 변환 완료! 이제 원래 폴더에 '_openvino_model' 이라는 이름이 붙은 폴더가 생성되었습니다.")
print("이제 [yolo_초고속_openvino_트래킹.py] 파일을 실행해 보세요!")
