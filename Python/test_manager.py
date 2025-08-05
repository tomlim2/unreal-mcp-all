#!/usr/bin/env python3
"""
Unreal MCP 테스트 관리자

scripts 폴더에 카테고리별로 정리된 테스트 파일들을 관리하고 실행할 수 있는 도구입니다.

카테고리:
- actors: 액터 관련 테스트
- blueprints: 블루프린트 관련 테스트  
- sky: 스카이/날씨 관련 테스트
- node: 노드/컴포넌트 관련 테스트
- tests: 기타 통합 테스트
"""

import os
import sys
import importlib.util
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestManager:
    """테스트 파일들을 관리하는 클래스"""
    
    def __init__(self, scripts_dir: str = "scripts"):
        """초기화
        
        Args:
            scripts_dir: 스크립트 디렉토리 경로
        """
        self.scripts_dir = Path(scripts_dir)
        self.categories = self._discover_categories()
        
    def _discover_categories(self) -> Dict[str, List[Path]]:
        """카테고리별 테스트 파일들을 검색합니다."""
        categories = {}
        
        if not self.scripts_dir.exists():
            logger.warning(f"Scripts 디렉토리가 존재하지 않습니다: {self.scripts_dir}")
            return categories
            
        # 각 하위 디렉토리를 카테고리로 취급
        for category_dir in self.scripts_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith("__"):
                category_name = category_dir.name
                test_files = []
                
                # 테스트 파일들 찾기 (test_*.py 또는 *_test.py)
                for file_path in category_dir.rglob("*.py"):
                    if (file_path.name.startswith("test_") or 
                        file_path.name.endswith("_test.py") or
                        "test" in file_path.name.lower()):
                        test_files.append(file_path)
                
                if test_files:
                    categories[category_name] = sorted(test_files)
                    
        return categories
    
    def list_categories(self) -> List[str]:
        """사용 가능한 카테고리 목록을 반환합니다."""
        return list(self.categories.keys())
    
    def list_tests(self, category: str = None) -> Dict[str, List[str]]:
        """테스트 파일 목록을 반환합니다.
        
        Args:
            category: 특정 카테고리만 조회 (None이면 전체)
            
        Returns:
            카테고리별 테스트 파일 목록
        """
        if category:
            if category in self.categories:
                return {category: [str(f.relative_to(self.scripts_dir)) for f in self.categories[category]]}
            else:
                return {}
        else:
            return {cat: [str(f.relative_to(self.scripts_dir)) for f in files] 
                   for cat, files in self.categories.items()}
    
    def run_test(self, test_path: str, python_exe: str = None) -> Dict[str, Any]:
        """테스트 파일을 실행합니다.
        
        Args:
            test_path: 테스트 파일 경로 (scripts 디렉토리 기준 상대 경로)
            python_exe: 사용할 Python 실행 파일 경로
            
        Returns:
            실행 결과 정보
        """
        full_path = self.scripts_dir / test_path
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"테스트 파일이 존재하지 않습니다: {full_path}",
                "output": ""
            }
        
        if python_exe is None:
            python_exe = sys.executable
            
        try:
            logger.info(f"테스트 실행 중: {test_path}")
            
            # 테스트 파일 실행
            result = subprocess.run(
                [python_exe, str(full_path)],
                cwd=os.getcwd(),  # 프로젝트 루트에서 실행
                capture_output=True,
                text=True,
                timeout=120  # 2분 타임아웃
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "output": result.stdout,
                "error": result.stderr,
                "test_path": str(test_path)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "테스트 실행 시간 초과 (2분)",
                "output": "",
                "test_path": str(test_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"테스트 실행 중 오류: {str(e)}",
                "output": "",
                "test_path": str(test_path)
            }
    
    def run_category_tests(self, category: str, python_exe: str = None) -> List[Dict[str, Any]]:
        """특정 카테고리의 모든 테스트를 실행합니다.
        
        Args:
            category: 카테고리 이름
            python_exe: 사용할 Python 실행 파일 경로
            
        Returns:
            각 테스트 실행 결과 목록
        """
        if category not in self.categories:
            return [{
                "success": False,
                "error": f"카테고리를 찾을 수 없습니다: {category}",
                "output": ""
            }]
        
        results = []
        for test_file in self.categories[category]:
            relative_path = test_file.relative_to(self.scripts_dir)
            result = self.run_test(str(relative_path), python_exe)
            results.append(result)
            
        return results

def display_help():
    """도움말을 출력합니다."""
    print("""
🚀 Unreal MCP 테스트 관리자

사용법:
    python test_manager.py [명령] [옵션]

명령:
    list                    - 모든 카테고리와 테스트 목록 표시
    list <category>         - 특정 카테고리의 테스트 목록 표시
    run <test_path>         - 특정 테스트 실행
    run-category <category> - 카테고리의 모든 테스트 실행
    help                    - 이 도움말 표시

예시:
    python test_manager.py list
    python test_manager.py list actors
    python test_manager.py run actors/test_cube.py
    python test_manager.py run-category sky

카테고리:
    actors     - 액터 관련 테스트
    blueprints - 블루프린트 관련 테스트
    sky        - 스카이/날씨 관련 테스트
    node       - 노드/컴포넌트 관련 테스트
    tests      - 기타 통합 테스트
    """)

def main():
    """메인 함수"""
    args = sys.argv[1:] if len(sys.argv) > 1 else ["help"]
    
    # Python 실행 파일 경로 설정
    python_exe = "E:/UnrealMCP/unreal-mcp-main/unreal-mcp-main/Python/.venv/Scripts/python.exe"
    
    manager = TestManager()
    
    command = args[0].lower()
    
    if command == "help":
        display_help()
        
    elif command == "list":
        if len(args) > 1:
            # 특정 카테고리 목록
            category = args[1]
            tests = manager.list_tests(category)
            if tests:
                print(f"\n📂 {category} 카테고리 테스트:")
                print("=" * 40)
                for test in tests[category]:
                    print(f"  - {test}")
            else:
                print(f"❌ 카테고리를 찾을 수 없습니다: {category}")
        else:
            # 전체 목록
            print("\n📋 사용 가능한 테스트 카테고리:")
            print("=" * 50)
            
            tests = manager.list_tests()
            for category, test_files in tests.items():
                print(f"\n📂 {category} ({len(test_files)}개)")
                print("-" * 30)
                for test in test_files:
                    print(f"  - {test}")
                    
    elif command == "run":
        if len(args) < 2:
            print("❌ 실행할 테스트 파일을 지정해주세요.")
            print("   예: python test_manager.py run actors/test_cube.py")
            return
            
        test_path = args[1]
        print(f"🚀 테스트 실행: {test_path}")
        print("=" * 50)
        
        result = manager.run_test(test_path, python_exe)
        
        if result["success"]:
            print("✅ 테스트 성공!")
            if result["output"]:
                print("\n📤 출력:")
                print(result["output"])
        else:
            print("❌ 테스트 실패!")
            if result["error"]:
                print("\n🚨 오류:")
                print(result["error"])
            if result["output"]:
                print("\n📤 출력:")
                print(result["output"])
                
    elif command == "run-category":
        if len(args) < 2:
            print("❌ 실행할 카테고리를 지정해주세요.")
            print("   예: python test_manager.py run-category actors")
            return
            
        category = args[1]
        print(f"🚀 카테고리 테스트 실행: {category}")
        print("=" * 50)
        
        results = manager.run_category_tests(category, python_exe)
        
        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)
        
        print(f"\n📊 실행 결과: {success_count}/{total_count} 성공")
        print("=" * 30)
        
        for result in results:
            test_name = result.get("test_path", "Unknown")
            if result["success"]:
                print(f"✅ {test_name}")
            else:
                print(f"❌ {test_name}")
                if result["error"]:
                    print(f"   오류: {result['error']}")
    else:
        print(f"❌ 알 수 없는 명령: {command}")
        display_help()

if __name__ == "__main__":
    main()
