import cv2
import os
import subprocess
import glob
import easyocr
import firebase_admin
from firebase_admin import credentials, firestore, db
import tkinter as tk
import requests


# Firebase 프로젝트 설정
cred = credentials.Certificate("license-d68c6-firebase-adminsdk-rvher-328ef35868.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://license-d68c6-default-rtdb.firebaseio.com'})

# Firestore 인스턴스 얻기
db = firestore.client()

def show_message(result):
    # 메시지 창 생성
    popup = tk.Tk()
    popup.title("차량 확인 결과")

    # 결과를 표시하는 라벨
    label = tk.Label(popup, text=result)
    label.pack(padx=10, pady=10)

    # 닫기 버튼
    close_button = tk.Button(popup, text="닫기", command=popup.destroy)
    close_button.pack(pady=10)

    # 메시지 창 실행
    popup.mainloop()

def get_latest_exp_path(detect_path):
    exp_folders = glob.glob(os.path.join(detect_path, 'exp*'))
    if exp_folders:
        latest_exp_path = max(exp_folders, key=os.path.getctime)
        return latest_exp_path
    else:
        return None

# Firebase Realtime Database에서 '/parking_spot_state/A1' 값을 가져오는 함수
def get_parking_spot_state_values():
    url_A1 = 'https://license-d68c6-default-rtdb.firebaseio.com/parking_spot_state/A1.json'
    url_A2 = 'https://license-d68c6-default-rtdb.firebaseio.com/parking_spot_state/A2.json'

    response_A1 = requests.get(url_A1)
    response_A2 = requests.get(url_A2)

    data_A1 = response_A1.json()
    data_A2 = response_A2.json()

    return data_A1, data_A2

def main():
    count = 0
    count1 = 0
    count2 = 0

    while True:
        # Firebase에서 '/parking_spot_state/A1' 및 '/parking_spot_state/A2' 값 가져오기
        A1_value, A2_value = get_parking_spot_state_values()

        # A1 값 처리
        if A1_value:
            if count1 == 0:
                external_camera_index = 1  # 연결한 외부 웹 카메라 인덱스
                cap = cv2.VideoCapture(external_camera_index)

                # 웹캠 프레임 읽기
                ret, frame = cap.read()

                # 캡쳐된 화면 저장 경로
                save_path = r'C:/capstone/yolov5-master/assets'

                # 디렉토리가 없으면 생성
                if not os.path.exists(save_path):
                    os.makedirs(save_path)

                # 캡쳐한 화면 저장
                if ret:
                    img_path = os.path.join(save_path, f"captured_frame_{count}.jpg")
                    cv2.imwrite(img_path, frame)
                    print(f"화면을 {img_path}에 캡쳐했습니다.")

                    # Run object detection command
                    command = r"python detect.py --weights best.pt --save-txt --conf 0.7 --source {}".format(img_path)
                    subprocess.run(command, shell=True)

                    # Get the latest experiment path
                    latest_exp_path = get_latest_exp_path(r'C:/capstone/yolov5-master/runs/detect')

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
                        file = f"C:/capstone/yolov5-master/assets/cropped_frame_{count}_{i}.jpg"
                        reader = easyocr.Reader(['ko'], gpu=False)
                        img = cv2.imread(file)
                        text_list = reader.readtext(img, detail=0)

                        # 리스트의 각 문자열을 공백으로 연결하여 출력
                        combined_text = ' '.join(text_list)
                        print(combined_text)

                        registered_ref = db.collection("registered").document("car_license")
                        registered_doc = registered_ref.get()

                        if registered_doc.exists:
                            # 등록된 차량의 필드 값을 가져와서 OCR 결과와 일일히 비교
                            registered_data = registered_doc.to_dict()

                            # OCR 결과와 등록된 차량 필드 값 비교
                            for field, value in registered_data.items():
                                if value == combined_text:
                                    # 일치하는 값이 존재하면 Firebase Realtime Database 업데이트
                                    ref = firebase_admin.db.reference('/parking_spot_registered/A1')  # '/parking_spot_registered/A1'는 업데이트할 데이터 경로
                                    ref.set(True)  # True로 업데이트
                                    show_message("등록차량입니다.")
                                    break
                            else:
                                # 일치하는 값이 존재하지 않으면 Firebase Realtime Database 업데이트
                                ref = firebase_admin.db.reference('/parking_spot_registered/A1')  # '/parking_spot_registered/A1'는 업데이트할 데이터 경로
                                ref.set(False)  # False로 업데이트
                                show_message("비등록차량입니다.")
                        else:
                            # 등록된 차량 문서가 없을 경우 Firebase Realtime Database 업데이트
                            ref = firebase_admin.db.reference('/parking_spot_registered/A1')  # '/parking_spot_registered/A1'는 업데이트할 데이터 경로
                            ref.set(False)  # False로 업데이트
                            show_message("비등록차량입니다.")

                else:
                    print("화면 캡쳐에 실패했습니다.")

                # 웹캠 종료
                cap.release()
                cv2.destroyAllWindows()  # 이 부분은 루프 바깥으로 이동
                count1 += 1
        else:
            count1 = 0

        # A2 값 처리
        if A2_value:
            if count2 == 0:
                external_camera_index = 1  # 연결한 외부 웹 카메라 인덱스
                cap = cv2.VideoCapture(external_camera_index)

                # 웹캠 프레임 읽기
                ret, frame = cap.read()

                # 캡쳐된 화면 저장 경로
                save_path = r'C:/capstone/yolov5-master/assets'

                # 디렉토리가 없으면 생성
                if not os.path.exists(save_path):
                    os.makedirs(save_path)

                # 캡쳐한 화면 저장
                if ret:
                    img_path = os.path.join(save_path, f"captured_frame_{count}.jpg")
                    cv2.imwrite(img_path, frame)
                    print(f"화면을 {img_path}에 캡쳐했습니다.")

                    # Run object detection command
                    command = r"python detect.py --weights best.pt --save-txt --conf 0.7 --source {}".format(img_path)
                    subprocess.run(command, shell=True)

                    # Get the latest experiment path
                    latest_exp_path = get_latest_exp_path(r'C:/capstone/yolov5-master/runs/detect')

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
                        file = f"C:/capstone/yolov5-master/assets/cropped_frame_{count}_{i}.jpg"
                        reader = easyocr.Reader(['ko'], gpu=False)
                        img = cv2.imread(file)
                        text_list = reader.readtext(img, detail=0)

                        # 리스트의 각 문자열을 공백으로 연결하여 출력
                        combined_text = ' '.join(text_list)
                        print(combined_text)

                        registered_ref = db.collection("registered").document("car_license")
                        registered_doc = registered_ref.get()

                        if registered_doc.exists:
                            # 등록된 차량의 필드 값을 가져와서 OCR 결과와 일일히 비교
                            registered_data = registered_doc.to_dict()

                            # OCR 결과와 등록된 차량 필드 값 비교
                            for field, value in registered_data.items():
                                if value == combined_text:
                                    # 일치하는 값이 존재하면 Firebase Realtime Database 업데이트
                                    ref = firebase_admin.db.reference('/parking_spot_registered/A2')  # '/parking_spot_registered/A2'는 업데이트할 데이터 경로
                                    ref.set(True)  # True로 업데이트
                                    show_message("등록차량입니다.")
                                    break
                            else:
                                # 일치하는 값이 존재하지 않으면 Firebase Realtime Database 업데이트
                                ref = firebase_admin.db.reference('/parking_spot_registered/A2')  # '/parking_spot_registered/A2'는 업데이트할 데이터 경로
                                ref.set(False)  # False로 업데이트
                                show_message("비등록차량입니다.")
                        else:
                            # 등록된 차량 문서가 없을 경우 Firebase Realtime Database 업데이트
                            ref = firebase_admin.db.reference('/parking_spot_registered/A2')  # '/parking_spot_registered/A2'는 업데이트할 데이터 경로
                            ref.set(False)  # False로 업데이트
                            show_message("비등록차량입니다.")

                else:
                    print("화면 캡쳐에 실패했습니다.")

                # 웹캠 종료
                cap.release()
                cv2.destroyAllWindows()  # 이 부분은 루프 바깥으로 이동
                count2 += 1
        else:
            count2 = 0

if __name__ == "__main__":
    main()
