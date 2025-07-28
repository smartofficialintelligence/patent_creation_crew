#!/usr/bin/env python3
"""
Retry Wrapper Tool for Patent Automation System
Wraps existing tools with retry logic and error recovery
"""

import logging
from typing import Dict, Any, Callable, Optional
try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai.tools.agent_tools import Tool as BaseTool

logger = logging.getLogger(__name__)

class RetryWrapperTool(BaseTool):
    """Wrapper tool that adds retry logic to existing tools"""
    
    name: str = "retry_wrapper_tool"
    description: str = "Retry-enabled wrapper for existing tools"
    
    def __init__(self, 
                 wrapped_tool: BaseTool,
                 retry_manager,
                 tool_name: str,
                 max_retries: int = 3):
        super().__init__()
        # Store wrapped tool as instance variable, not field
        self._wrapped_tool = wrapped_tool
        self._retry_manager = retry_manager
        self._tool_name = tool_name
        self._max_retries = max_retries
        
        # Copy attributes from wrapped tool
        self.name = f"retry_{wrapped_tool.name}"
        self.description = f"Retry-enabled version of {wrapped_tool.description}"
        
    def _run(self, *args, **kwargs) -> str:
        """Execute the wrapped tool with retry logic"""
        # Extract patent_id from arguments if available
        patent_id = kwargs.get('patent_id', 'unknown')
        if not patent_id and args:
            # Try to get patent_id from first argument if it's a dict
            if isinstance(args[0], dict):
                patent_id = args[0].get('id', 'unknown')
        
        # Use the retry manager to execute the tool
        def tool_function(*tool_args, **tool_kwargs):
            return self._wrapped_tool._run(*tool_args, **tool_kwargs)
        
        try:
            result = self._retry_manager.execute_with_retry(
                patent_id=patent_id,
                tool_name=self._tool_name,
                tool_function=tool_function,
                *args,
                **kwargs
            )
            return result
        except Exception as e:
            logger.error(f"RetryWrapperTool failed for {self._tool_name}: {e}")
            return f"ERROR IN RETRY WRAPPER: {str(e)}"

def create_retry_wrapped_tools(tools: Dict[str, BaseTool], retry_manager) -> Dict[str, RetryWrapperTool]:
    """Create retry-wrapped versions of all tools"""
    wrapped_tools = {}
    
    for tool_name, tool in tools.items():
        try:
            wrapped_tool = RetryWrapperTool(
                wrapped_tool=tool,
                retry_manager=retry_manager,
                tool_name=tool_name
            )
            wrapped_tools[tool_name] = wrapped_tool
            logger.info(f"Created retry wrapper for {tool_name}")
        except Exception as e:
            logger.error(f"Failed to create retry wrapper for {tool_name}: {e}")
            # Keep original tool if wrapper creation fails
            wrapped_tools[tool_name] = tool
    
    return wrapped_tools 