import cv2
import os
import subprocess
import glob
import easyocr


def get_latest_exp_path(detect_path):
    exp_folders = glob.glob(os.path.join(detect_path, 'exp*'))
    if exp_folders:
        latest_exp_path = max(exp_folders, key=os.path.getctime)
        return latest_exp_path
    else:
        return None


# 사용자로부터 숫자 입력 받기
count = 0
while True:
    # if 문을 사용하여 조건 검사
    user_input = int(input("숫자를 입력하세요: "))
    if user_input >= 4:
        # 웹캠 열기
        external_camera_index = 1  # 연결한 외부 웹 카메라 인덱스
        cap = cv2.VideoCapture(external_camera_index)

        # 웹캠 프레임 읽기
        ret, frame = cap.read()

        # 캡쳐된 화면 저장 경로
        save_path = r'C:\storeIMG'

        # 디렉토리가 없으면 생성
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # 캡쳐한 화면 저장
        if ret:
            img_path = os.path.join(save_path, f"captured_frame_{count}.jpg")
            cv2.imwrite(img_path, frame)
            print(f"화면을 {img_path}에 캡쳐했습니다.")

            # Run object detection command
            command = r"python detect.py --weights best.pt --save-txt --conf 0.5 --source {}".format(img_path)
            subprocess.run(command, shell=True)

            # Get the latest experiment path
            latest_exp_path = get_latest_exp_path(r'C:\yolov5-master\runs\detect')

            if latest_exp_path:
                # Read the bounding box coordinates from the generated txt file
                file_path = os.path.join(latest_exp_path, 'labels', f"captured_frame_{count}.txt")
            count += 1

            # 변수 초기화
            x_list = []
            y_list = []
            w_list = []
            h_list = []

            # 파일 읽기
            with open(file_path, 'r') as file:
                lines = file.readlines()

            # 각 줄의 숫자를 변수에 매핑
            for line in lines:
                data = line.strip().split(' ')

                # 클래스 인덱스는 무시
                x = float(data[1])
                y = float(data[2])
                w = float(data[3])
                h = float(data[4])

                # 변수에 추가
                x_list.append(x)
                y_list.append(y)
                w_list.append(w)
                h_list.append(h)

            # 결과 출력
            for i in range(len(x_list)):
                print(f"Box {i + 1}: x={x_list[i]}, y={y_list[i]}, w={w_list[i]}, h={h_list[i]}")

            # 이미지에서 관심 영역 추출 및 저장
            for i in range(len(x_list)):
                print(f"Box {i + 1}: x={x_list[i]}, y={y_list[i]}, w={w_list[i]}, h={h_list[i]}")

                # 이미지에서 관심 영역 추출
                x_min = int((x_list[i] - w_list[i] / 2) * frame.shape[1])
                y_min = int((y_list[i] - h_list[i] / 2) * frame.shape[0])
                x_max = int((x_list[i] + w_list[i] / 2) * frame.shape[1])
                y_max = int((y_list[i] + h_list[i] / 2) * frame.shape[0])

                roi = frame[y_min:y_max, x_min:x_max]

                # 새로운 이미지 저장 경로
                new_img_path = os.path.join(save_path, f"cropped_frame_{count}_{i}.jpg")

                # 새로운 이미지 저장
                cv2.imwrite(new_img_path, roi)
                print(f"ROI를 {new_img_path}에 저장했습니다.")

                # OCR 수행
                file = f"C:\storeIMG\cropped_frame_{count}_{i}.jpg"
                reader = easyocr.Reader(['ko'], gpu=False)
                img = cv2.imread(file)
                text_list = reader.readtext(img, detail=0)

                # 리스트의 각 문자열을 공백으로 연결하여 출력
                combined_text = ' '.join(text_list)
                print(combined_text)

        else:
            print("화면 캡쳐에 실패했습니다.")

        # 웹캠 종료
        cap.release()
        cv2.destroyAllWindows()  # 이 부분은 루프 바깥으로 이동
    else:
        print("입력된 숫자가 4 미만입니다.")
        break

