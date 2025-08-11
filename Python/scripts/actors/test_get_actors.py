#!/usr/bin/env python3
"""
액터 조회 테스트

레벨의 모든 액터를 조회하고 정보를 출력하는 테스트입니다.
카테고리: actors
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

def test_get_actors():
    """액터 조회 테스트 함수"""
    try:
        print("🔌 Unreal Engine에 연결 중...")
        
        # 액터 목록 조회
        response = send_command("get_actors_in_level", {})
        if response and response.get("status") == "success":
            actors = response["result"]["actors"]
            print(f"📋 레벨에 {len(actors)}개의 액터가 있습니다.")
            
            # 액터 타입별 분류
            actor_types = {}
            for actor in actors:
                actor_class = actor.get("class", "Unknown")
                if actor_class not in actor_types:
                    actor_types[actor_class] = []
                actor_types[actor_class].append(actor["name"])
            
            # 결과 출력
            print("\n📂 액터 타입별 분류:")
            for actor_type, names in sorted(actor_types.items()):
                print(f"  {actor_type}: {len(names)}개")
                for name in names[:3]:  # 처음 3개만 표시
                    print(f"    - {name}")
                if len(names) > 3:
                    print(f"    ... 외 {len(names) - 3}개")
            
            print("✅ 액터 조회 테스트 완료!")
            return True
        else:
            print("❌ 액터 목록 조회 실패")
            if response:
                print(f"   응답: {response}")
            return False
        
    except Exception as e:
        print(f"❌ 액터 조회 테스트 중 오류 발생: {e}")
        logger.error(f"액터 조회 테스트 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_get_actors()
    exit(0 if success else 1)