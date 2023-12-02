import cv2

# 시도할 카메라 인덱스의 범위 지정
min_index = 0
max_index = 10  # 최대 인덱스를 적절히 조절하세요

for i in range(min_index, max_index + 1):
    cap = cv2.VideoCapture(i)

    # 카메라가 열렸는지 확인
    if not cap.isOpened():
        print(f"카메라 인덱스 {i}는 열 수 없습니다.")
    else:
        print(f"카메라 인덱스 {i}가 열렸습니다.")

    # 열려있는 카메라를 해제
    cap.release()
