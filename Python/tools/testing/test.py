"""
Test Management Tools for Unreal MCP.

This module provides tools for managing and running categorized test scripts.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP, Context

# Get logger
logger = logging.getLogger("UnrealMCP")

def register_test_tools(mcp: FastMCP):
    """Register test management tools with the MCP server."""
    
    @mcp.tool()
    def list_test_categories(ctx: Context) -> List[str]:
        """List all available test categories in the scripts directory.
        
        Returns:
            List of category names
        """
        try:
            scripts_dir = Path("scripts")
            categories = []
            
            if not scripts_dir.exists():
                logger.warning("Scripts directory does not exist")
                return []
                
            for category_dir in scripts_dir.iterdir():
                if category_dir.is_dir() and not category_dir.name.startswith("__"):
                    # Check if category has test files
                    test_files = list(category_dir.rglob("*.py"))
                    if test_files:
                        categories.append(category_dir.name)
            
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error listing test categories: {e}")
            return []
    
    @mcp.tool()
    def list_tests_in_category(ctx: Context, category: str) -> List[Dict[str, Any]]:
        """List all test files in a specific category.
        
        Args:
            category: The category name to list tests from
            
        Returns:
            List of test file information
        """
        try:
            scripts_dir = Path("scripts")
            category_dir = scripts_dir / category
            
            if not category_dir.exists():
                logger.warning(f"Category directory does not exist: {category}")
                return []
                
            test_files = []
            for file_path in category_dir.rglob("*.py"):
                if (file_path.name.startswith("test_") or 
                    file_path.name.endswith("_test.py") or
                    "test" in file_path.name.lower()):
                    
                    relative_path = file_path.relative_to(scripts_dir)
                    test_files.append({
                        "name": file_path.name,
                        "path": str(relative_path),
                        "category": category,
                        "full_path": str(file_path)
                    })
            
            return sorted(test_files, key=lambda x: x["name"])
            
        except Exception as e:
            logger.error(f"Error listing tests in category {category}: {e}")
            return []
    
    @mcp.tool()
    def run_test_file(ctx: Context, test_path: str, python_exe: str = None) -> Dict[str, Any]:
        """Run a specific test file.
        
        Args:
            test_path: Path to test file relative to scripts directory
            python_exe: Python executable path (optional)
            
        Returns:
            Test execution result
        """
        try:
            scripts_dir = Path("scripts")
            full_path = scripts_dir / test_path
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Test file not found: {full_path}",
                    "output": ""
                }
            
            if python_exe is None:
                # Use the virtual environment Python
                python_exe = "E:/UnrealMCP/unreal-mcp-main/unreal-mcp-main/Python/.venv/Scripts/python.exe"
                
            logger.info(f"Running test: {test_path}")
            
            # Run the test file
            result = subprocess.run(
                [python_exe, str(full_path)],
                cwd=str(full_path.parent),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "output": result.stdout,
                "error": result.stderr,
                "test_path": test_path
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out (2 minutes)",
                "output": "",
                "test_path": test_path
            }
        except Exception as e:
            logger.error(f"Error running test {test_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "test_path": test_path
            }
    
    @mcp.tool()
    def run_category_tests(ctx: Context, category: str, python_exe: str = None) -> List[Dict[str, Any]]:
        """Run all tests in a specific category.
        
        Args:
            category: Category name to run tests from
            python_exe: Python executable path (optional)
            
        Returns:
            List of test execution results
        """
        try:
            # Get all tests in the category
            tests = list_tests_in_category(ctx, category)
            
            if not tests:
                return [{
                    "success": False,
                    "error": f"No tests found in category: {category}",
                    "output": ""
                }]
            
            results = []
            for test_info in tests:
                result = run_test_file(ctx, test_info["path"], python_exe)
                result["test_name"] = test_info["name"]
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error running category tests {category}: {e}")
            return [{
                "success": False,
                "error": str(e),
                "output": ""
            }]
    
    @mcp.tool()
    def get_test_summary(ctx: Context) -> Dict[str, Any]:
        """Get a summary of all available tests organized by category.
        
        Returns:
            Summary of test organization
        """
        try:
            categories = list_test_categories(ctx)
            summary = {
                "total_categories": len(categories),
                "categories": {}
            }
            
            total_tests = 0
            for category in categories:
                tests = list_tests_in_category(ctx, category)
                summary["categories"][category] = {
                    "test_count": len(tests),
                    "tests": [t["name"] for t in tests]
                }
                total_tests += len(tests)
            
            summary["total_tests"] = total_tests
            return summary
            
        except Exception as e:
            logger.error(f"Error getting test summary: {e}")
            return {
                "total_categories": 0,
                "total_tests": 0,
                "categories": {},
                "error": str(e)
            }
    
    @mcp.tool()
    def create_test_file(ctx: Context, category: str, test_name: str, template: str = "basic") -> Dict[str, Any]:
        """Create a new test file in the specified category.
        
        Args:
            category: Category to create the test in
            test_name: Name of the test file (without .py extension)
            template: Template type to use ("basic", "actor", "blueprint", "sky")
            
        Returns:
            Result of test file creation
        """
        try:
            scripts_dir = Path("scripts")
            category_dir = scripts_dir / category
            
            # Create category directory if it doesn't exist
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Ensure test name starts with "test_"
            if not test_name.startswith("test_"):
                test_name = f"test_{test_name}"
            
            # Ensure .py extension
            if not test_name.endswith(".py"):
                test_name = f"{test_name}.py"
                
            test_file_path = category_dir / test_name
            
            if test_file_path.exists():
                return {
                    "success": False,
                    "error": f"Test file already exists: {test_file_path}",
                    "path": str(test_file_path)
                }
            
            # Get template content
            template_content = get_test_template(template, test_name, category)
            
            # Write the test file
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            return {
                "success": True,
                "message": f"Created test file: {test_name}",
                "path": str(test_file_path),
                "category": category
            }
            
        except Exception as e:
            logger.error(f"Error creating test file {test_name} in {category}: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": ""
            }

def get_test_template(template_type: str, test_name: str, category: str) -> str:
    """Get template content for a new test file.
    
    Args:
        template_type: Type of template
        test_name: Name of the test file
        category: Category the test belongs to
        
    Returns:
        Template content as string
    """
    basic_template = f'''#!/usr/bin/env python3
"""
{test_name.replace('_', ' ').title()}

테스트 설명을 여기에 작성하세요.
카테고리: {category}
"""

import logging
from unreal_mcp_server import get_unreal_connection

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_main():
    """메인 테스트 함수"""
    try:
        # Unreal Engine 연결
        unreal = get_unreal_connection()
        if not unreal:
            print("❌ Unreal Engine에 연결할 수 없습니다.")
            return False
        
        print("🔌 Unreal Engine에 연결되었습니다.")
        
        # TODO: 여기에 테스트 로직을 구현하세요
        
        print("✅ 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {{e}}")
        logger.error(f"테스트 오류: {{e}}")
        return False

if __name__ == "__main__":
    success = test_main()
    exit(0 if success else 1)
'''
    
    actor_template = f'''#!/usr/bin/env python3
"""
{test_name.replace('_', ' ').title()}

액터 관련 테스트
카테고리: {category}
"""

import logging
from unreal_mcp_server import get_unreal_connection

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_actor_operations():
    """액터 관련 테스트 함수"""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            print("❌ Unreal Engine에 연결할 수 없습니다.")
            return False
        
        print("🔌 Unreal Engine에 연결되었습니다.")
        
        # 액터 목록 조회
        response = unreal.send_command("get_actors_in_level", {{}})
        if response and response.get("status") == "success":
            actors = response["result"]["actors"]
            print(f"📋 레벨에 {{len(actors)}}개의 액터가 있습니다.")
        else:
            print("❌ 액터 목록 조회 실패")
            return False
        
        # TODO: 추가 액터 테스트 로직
        
        print("✅ 액터 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 액터 테스트 중 오류 발생: {{e}}")
        logger.error(f"액터 테스트 오류: {{e}}")
        return False

if __name__ == "__main__":
    success = test_actor_operations()
    exit(0 if success else 1)
'''
    
    sky_template = f'''#!/usr/bin/env python3
"""
{test_name.replace('_', ' ').title()}

스카이/날씨 관련 테스트
카테고리: {category}
"""

import logging
from unreal_mcp_server import get_unreal_connection

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sky_operations():
    """스카이 관련 테스트 함수"""
    try:
        unreal = get_unreal_connection()
        if not unreal:
            print("❌ Unreal Engine에 연결할 수 없습니다.")
            return False
        
        print("🔌 Unreal Engine에 연결되었습니다.")
        
        # 현재 시간 조회
        response = unreal.send_command("get_time_of_day", {{"sky_name": "Ultra_Dynamic_Sky_C_0"}})
        if response and response.get("status") == "success":
            current_time = response["result"]["time_of_day"]
            print(f"🕐 현재 시간: {{current_time}}")
        else:
            print("❌ 시간 조회 실패")
            return False
        
        # TODO: 추가 스카이 테스트 로직
        
        print("✅ 스카이 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 스카이 테스트 중 오류 발생: {{e}}")
        logger.error(f"스카이 테스트 오류: {{e}}")
        return False

if __name__ == "__main__":
    success = test_sky_operations()
    exit(0 if success else 1)
'''
    
    templates = {
        "basic": basic_template,
        "actor": actor_template,
        "sky": sky_template,
        "blueprint": basic_template  # 나중에 별도 템플릿 추가 가능
    }
    
    return templates.get(template_type, basic_template)

# Register tools
logger.info("Test management tools registered successfully")
