"""
Multi-Tool Orchestrator for Creative Hub

Coordinates workflows that span multiple tools (Unreal Engine, Nano Banana, etc.)
and manages command routing based on tool capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from core import get_registry, ToolCapability, CommandResult

logger = logging.getLogger("UnrealMCP.Orchestrator")


@dataclass
class WorkflowStep:
    """Represents a single step in a multi-tool workflow."""
    step_id: str
    tool_id: str
    command_type: str
    params: Dict[str, Any]
    depends_on: Optional[List[str]] = None  # List of step_ids this step depends on
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[CommandResult] = None


class WorkflowOrchestrator:
    """
    Orchestrates multi-tool workflows with dependency management.

    Features:
    - Route commands to appropriate tools based on capabilities
    - Manage workflow state across multiple steps
    - Handle inter-tool data passing (e.g., screenshot → image edit)
    - Provide rollback on failures
    """

    def __init__(self):
        self._registry = get_registry()
        self._active_workflows: Dict[str, List[WorkflowStep]] = {}

    def route_command(
        self,
        command_type: str,
        params: Dict[str, Any],
        preferred_tool: Optional[str] = None
    ) -> CommandResult:
        """
        Route a single command to the appropriate tool.

        Args:
            command_type: Command to execute
            params: Command parameters
            preferred_tool: Optional tool_id to prefer if multiple tools support command

        Returns:
            CommandResult from tool execution
        """
        # If preferred tool specified, try it first
        if preferred_tool:
            tool = self._registry.get_tool(preferred_tool)
            if tool and command_type in tool.get_supported_commands():
                logger.info(f"Routing {command_type} to preferred tool: {preferred_tool}")
                return tool.execute_command(command_type, params)
            else:
                logger.warning(
                    f"Preferred tool {preferred_tool} doesn't support {command_type}, "
                    f"falling back to registry"
                )

        # Otherwise use registry's default routing
        return self._registry.execute_command(command_type, params)

    def find_tools_by_capability(self, capability: ToolCapability) -> List[str]:
        """
        Find all tools that support a specific capability.

        Args:
            capability: ToolCapability to search for

        Returns:
            List of tool IDs supporting this capability
        """
        return self._registry.get_tools_by_capability(capability)

    def create_workflow(
        self,
        workflow_id: str,
        steps: List[WorkflowStep]
    ) -> bool:
        """
        Create a new multi-step workflow.

        Args:
            workflow_id: Unique workflow identifier
            steps: List of WorkflowStep objects

        Returns:
            True if workflow created successfully
        """
        if workflow_id in self._active_workflows:
            logger.warning(f"Workflow {workflow_id} already exists")
            return False

        self._active_workflows[workflow_id] = steps
        logger.info(f"Created workflow {workflow_id} with {len(steps)} steps")
        return True

    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute a multi-step workflow with dependency management.

        Args:
            workflow_id: Workflow to execute

        Returns:
            Dict with workflow results and status
        """
        if workflow_id not in self._active_workflows:
            return {
                'success': False,
                'error': f'Workflow not found: {workflow_id}'
            }

        steps = self._active_workflows[workflow_id]
        completed_steps = {}
        results = []

        # Execute steps in dependency order
        for step in steps:
            # Check dependencies
            if step.depends_on:
                dependencies_met = all(
                    dep_id in completed_steps and completed_steps[dep_id].success
                    for dep_id in step.depends_on
                )
                if not dependencies_met:
                    step.status = "failed"
                    step.result = CommandResult(
                        success=False,
                        error=f"Dependencies not met for step {step.step_id}",
                        error_code="DEPENDENCY_FAILED"
                    )
                    results.append({
                        'step_id': step.step_id,
                        'success': False,
                        'error': step.result.error
                    })
                    continue

            # Execute step
            logger.info(f"Executing step {step.step_id}: {step.command_type} on {step.tool_id}")
            step.status = "running"

            try:
                # Get tool and execute
                tool = self._registry.get_tool(step.tool_id)
                if not tool:
                    raise Exception(f"Tool not found: {step.tool_id}")

                step.result = tool.execute_command(step.command_type, step.params)
                step.status = "completed" if step.result.success else "failed"

                # Track completion
                if step.result.success:
                    completed_steps[step.step_id] = step.result

                results.append({
                    'step_id': step.step_id,
                    'success': step.result.success,
                    'result': step.result.result,
                    'error': step.result.error
                })

            except Exception as e:
                logger.error(f"Error executing step {step.step_id}: {e}")
                step.status = "failed"
                step.result = CommandResult(
                    success=False,
                    error=str(e),
                    error_code="EXECUTION_ERROR"
                )
                results.append({
                    'step_id': step.step_id,
                    'success': False,
                    'error': str(e)
                })

        # Determine overall workflow success
        all_success = all(step.status == "completed" for step in steps)

        return {
            'success': all_success,
            'workflow_id': workflow_id,
            'steps_completed': len([s for s in steps if s.status == "completed"]),
            'steps_total': len(steps),
            'results': results
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a workflow.

        Args:
            workflow_id: Workflow to check

        Returns:
            Status dict or None if workflow not found
        """
        if workflow_id not in self._active_workflows:
            return None

        steps = self._active_workflows[workflow_id]
        return {
            'workflow_id': workflow_id,
            'total_steps': len(steps),
            'pending': len([s for s in steps if s.status == "pending"]),
            'running': len([s for s in steps if s.status == "running"]),
            'completed': len([s for s in steps if s.status == "completed"]),
            'failed': len([s for s in steps if s.status == "failed"])
        }

    def cleanup_workflow(self, workflow_id: str) -> bool:
        """
        Remove completed or failed workflow from active list.

        Args:
            workflow_id: Workflow to cleanup

        Returns:
            True if removed successfully
        """
        if workflow_id in self._active_workflows:
            del self._active_workflows[workflow_id]
            logger.info(f"Cleaned up workflow: {workflow_id}")
            return True
        return False


# Global orchestrator instance
_orchestrator: Optional[WorkflowOrchestrator] = None


def get_orchestrator() -> WorkflowOrchestrator:
    """
    Get the global workflow orchestrator instance (singleton pattern).

    Returns:
        WorkflowOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorkflowOrchestrator()
    return _orchestrator


def reset_orchestrator() -> None:
    """Reset the global orchestrator (primarily for testing)."""
    global _orchestrator
    _orchestrator = None
