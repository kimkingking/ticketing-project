import subprocess
import time
import json

print("🚀 대기열 자동 펌프 가동 시작 (방식: 컨테이너 내부 Python 직접 실행)")

# 💡 curl이 없으므로, 백엔드 컨테이너의 Python을 이용해 127.0.0.1을 찌르는 명령어를 만듭니다.
cmd = [
    "kubectl", "exec", "deploy/ticket-backend-deploy", "--",
    "python", "-c",
    "import urllib.request; req=urllib.request.Request('http://127.0.0.1:8000/next?count=5', method='POST'); print(urllib.request.urlopen(req).read().decode())"
]

while True:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            try:
                data = json.loads(output)
                print(f"✅ 펌프 성공: {data.get('message', output)}")
            except json.JSONDecodeError:
                print(f"✅ 펌프 성공: {output}")
        else:
            print(f"⚠️ 통신 에러: {result.stderr.strip()}")
            
    except Exception as e:
        print(f"❌ 시스템 에러: {e}")
    
    time.sleep(1)
