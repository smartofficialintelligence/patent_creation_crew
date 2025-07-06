"""
Parameter Correction Wrapper
Automatically corrects common parameter name mistakes before calling tools.
"""

import logging
from typing import Dict, Any, Callable
from crewai.tools import BaseTool
from core.tool_parameter_mapping import validate_tool_parameters, get_tool_parameter_guide
from pydantic import Field

logger = logging.getLogger(__name__)

class ParameterCorrectionWrapper(BaseTool):
    """Wrapper that automatically corrects parameter names before calling tools."""
    
    tool_name: str = Field(...)
    original_tool: Any = Field(...)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, tool_name: str, original_tool):
        # Set fields for Pydantic
        super().__init__(
            name=original_tool.name,
            description=original_tool.description,
            args_schema=original_tool.args_schema,
            tool_name=tool_name,
            original_tool=original_tool
        )
        
    def _run(self, **kwargs):
        """Call the tool with corrected parameters."""
        # Log original parameters for debugging
        logger.info(f"Original parameters for {self.tool_name}: {kwargs}")
        
        # Validate and correct parameters
        corrected_params = validate_tool_parameters(self.tool_name, kwargs)
        
        # Log any corrections made
        if corrected_params != kwargs:
            logger.info(f"Parameter corrections for {self.tool_name}:")
            for key, value in corrected_params.items():
                if key not in kwargs:
                    logger.info(f"  Added: {key} = {value}")
            for key in kwargs:
                if key not in corrected_params:
                    logger.info(f"  Removed: {key}")
        
        # Call the original tool with corrected parameters
        try:
            result = self.original_tool._run(**corrected_params)
            return result
        except Exception as e:
            # If the tool still fails, provide helpful error message
            logger.error(f"Tool {self.tool_name} failed even after parameter correction: {e}")
            guide = get_tool_parameter_guide(self.tool_name)
            error_msg = f"Tool {self.tool_name} failed. Parameter guide:\n{guide}\n\nError: {e}"
            raise ValueError(error_msg)

def wrap_tool_with_parameter_correction(tool_name: str, tool_instance):
    """Wrap a tool instance with parameter correction."""
    return ParameterCorrectionWrapper(tool_name, tool_instance) 