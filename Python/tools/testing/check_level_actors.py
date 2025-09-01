#!/usr/bin/env python3
"""
레벨 액터 확인 스크립트

Unreal Engine 레벨에 있는 모든 액터들을 조회하고 정보를 출력합니다.
"""

import json
import logging
from unreal_mcp_server import get_unreal_connection

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_level_actors():
    """현재 레벨의 모든 액터를 가져옵니다."""
    try:
        # Unreal Engine 연결 가져오기
        unreal = get_unreal_connection()
        if not unreal:
            print("❌ Unreal Engine에 연결할 수 없습니다.")
            print("  - Unreal Engine이 실행되고 있는지 확인하세요")
            print("  - MCP 플러그인이 활성화되어 있는지 확인하세요")
            print("  - 포트 55557이 열려있는지 확인하세요")
            return []
        
        print("🔌 Unreal Engine에 연결되었습니다.")
        
        # 액터 목록 요청
        response = unreal.send_command("get_actors_in_level", {})
        
        if not response:
            print("❌ Unreal Engine으로부터 응답을 받지 못했습니다.")
            return []
        
        # 응답 처리
        if response.get("status") == "error":
            print(f"❌ 오류 발생: {response.get('error', '알 수 없는 오류')}")
            return []
        
        # 액터 데이터 추출
        actors = []
        if "result" in response and "actors" in response["result"]:
            actors = response["result"]["actors"]
        elif "actors" in response:
            actors = response["actors"]
        else:
            print(f"⚠️ 예상하지 못한 응답 형식: {response}")
            return []
        
        return actors
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        logger.error(f"레벨 액터 조회 중 오류: {e}")
        return []

def display_actors_info(actors):
    """액터 정보를 보기 좋게 출력합니다."""
    if not actors:
        print("📭 레벨에 액터가 없거나 조회할 수 없습니다.")
        return
    
    print(f"\n🎭 레벨 액터 목록 (총 {len(actors)}개)")
    print("=" * 60)
    
    # 액터 타입별로 그룹화
    actor_types = {}
    for actor in actors:
        actor_class = actor.get("class", "Unknown")
        if actor_class not in actor_types:
            actor_types[actor_class] = []
        actor_types[actor_class].append(actor)
    
    # 타입별로 출력
    for actor_type, type_actors in sorted(actor_types.items()):
        print(f"\n📂 {actor_type} ({len(type_actors)}개)")
        print("-" * 40)
        
        for i, actor in enumerate(type_actors, 1):
            name = actor.get("name", "Unnamed")
            location = actor.get("location", [])
            rotation = actor.get("rotation", [])
            scale = actor.get("scale", [])
            
            print(f"  {i}. {name}")
            
            # 위치 정보 출력 (배열 형태)
            if location and len(location) >= 3:
                x, y, z = location[0], location[1], location[2]
                print(f"     📍 위치: ({x:.2f}, {y:.2f}, {z:.2f})")
            
            # 회전 정보 출력
            if rotation and len(rotation) >= 3:
                pitch, yaw, roll = rotation[0], rotation[1], rotation[2]
                if pitch != 0 or yaw != 0 or roll != 0:
                    print(f"     � 회전: ({pitch:.2f}, {yaw:.2f}, {roll:.2f})")
            
            # 스케일 정보 출력
            if scale and len(scale) >= 3:
                sx, sy, sz = scale[0], scale[1], scale[2]
                if sx != 1 or sy != 1 or sz != 1:
                    print(f"     📏 스케일: ({sx:.2f}, {sy:.2f}, {sz:.2f})")
            
            # 클래스 정보 출력
            actor_class = actor.get("class")
            if actor_class:
                print(f"     🏷️ 클래스: {actor_class}")

def find_specific_actors():
    """특정 타입의 액터들을 찾습니다."""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            return
        
        # 일반적으로 찾을만한 액터 타입들
        common_types = [
            "StaticMeshActor",
            "PointLight", 
            "DirectionalLight",
            "Camera",
            "PlayerStart",
            "Ultra_Dynamic_Sky"
        ]
        
        print(f"\n🔍 특정 액터 타입 검색")
        print("=" * 40)
        
        for actor_type in common_types:
            response = unreal.send_command("find_actors_by_name", {
                "pattern": actor_type
            })
            
            if response and "actors" in response:
                actors = response["actors"]
                if actors:
                    print(f"✅ {actor_type}: {len(actors)}개 발견")
                    for actor in actors[:3]:  # 처음 3개만 표시
                        print(f"   - {actor}")
                else:
                    print(f"❌ {actor_type}: 없음")
            else:
                print(f"❓ {actor_type}: 조회 실패")
                
    except Exception as e:
        print(f"❌ 특정 액터 검색 중 오류: {e}")

def main():
    """메인 함수"""
    print("🚀 Unreal Engine 레벨 액터 확인 도구")
    print("=" * 50)
    
    # 모든 액터 조회
    actors = get_level_actors()
    display_actors_info(actors)
    
    # 특정 액터 타입 검색
    find_specific_actors()
    
    print(f"\n✅ 레벨 액터 확인 완료!")

if __name__ == "__main__":
    main()
