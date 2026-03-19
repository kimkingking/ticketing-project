import requests
import time

print(" 대기열 자동 펌프 가동 시작!")

while True:
    try:
        # 내 백엔드 서버의 /next 주소를 1초마다 찌릅니다.
        # 한번에 5명씩 들여보내도록 설정!
        response = requests.post("http://127.0.0.1:8000/next?count=10")

        if response.status_code == 200:
            print(f" 5명 입장 완료: {response.json()['message']}")
        else:
            print(" 대기열이 비어있거나 서버 응답이 없습니다.")

    except Exception as e:
        print(f" 연결 에러: {e}")

    # 1초 쉬고 다시 반복
    time.sleep(1)
