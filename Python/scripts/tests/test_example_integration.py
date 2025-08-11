#!/usr/bin/env python3
"""
예제 통합 테스트

기본 테스트 템플릿을 사용한 예제입니다.
카테고리: tests
"""

import json
import socket
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_command(command_type, params=None):
    """Unreal Engine에 명령을 전송합니다."""
    HOST = "127.0.0.1"
    PORT = 55557
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((HOST, PORT))
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        sock.sendall(json.dumps(command).encode('utf-8'))
        response = sock.recv(8192)
        result = json.loads(response.decode('utf-8'))
        sock.close()
        
        return result
        
    except Exception as e:
        logger.error(f"명령 전송 오류: {e}")
        return None

def test_main():
    """메인 테스트 함수"""
    try:
        print("🔌 Unreal Engine에 연결 중...")
        
        # 간단한 연결 테스트
        response = send_command("get_actors_in_level", {})
        if response and response.get("status") == "success":
            print("✅ Unreal Engine 연결 성공!")
            actors = response["result"]["actors"]
            print(f"📋 레벨에 {len(actors)}개의 액터가 있습니다.")
            return True
        else:
            print("❌ Unreal Engine 연결 실패")
            return False
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        logger.error(f"테스트 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_main()
    exit(0 if success else 1)
