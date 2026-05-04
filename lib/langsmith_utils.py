"""
LangSmith utilities for the patent pipeline
"""

import os
import logging
import yaml
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

class LangSmithManager:
    """Manages LangSmith configuration and tracing"""
    
    def __init__(self, config_path: str = "config/langsmith_config.yaml"):
        self.config_path = config_path
        self.client = None
        self.config = self._load_config()
        self._setup_langsmith()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load LangSmith configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('langsmith', {})
        except FileNotFoundError:
            logger.warning(f"LangSmith config file not found: {self.config_path}")
            return {}
        except Exception as e:
            logger.warning(f"Could not load LangSmith config: {e}")
            return {}
    
    def _setup_langsmith(self):
        """Setup LangSmith environment variables and client"""
        try:
            import langsmith
            from langsmith import Client
            
            # Check if API key is available (try both LANGCHAIN_API_KEY and LANGSMITH_API_KEY)
            api_key = os.getenv('LANGCHAIN_API_KEY') or os.getenv('LANGSMITH_API_KEY')
            if not api_key:
                logger.warning("Neither LANGCHAIN_API_KEY nor LANGSMITH_API_KEY is set. LangSmith monitoring will be disabled.")
                return
            
            # Set environment variables
            os.environ['LANGCHAIN_TRACING_V2'] = 'true'
            os.environ['LANGCHAIN_ENDPOINT'] = self.config.get('endpoint', 'https://api.smith.langchain.com')
            os.environ['LANGCHAIN_PROJECT'] = self.config.get('project', 'patent-pipeline')
            os.environ['LANGCHAIN_API_KEY'] = api_key  # Ensure it's set for LangSmith
            
            # Initialize client
            self.client = Client()
            logger.info("✅ LangSmith configured for monitoring and debugging")
            
        except ImportError:
            logger.warning("LangSmith not installed. Install with: pip install langsmith")
        except Exception as e:
            logger.warning(f"Could not setup LangSmith: {e}")
    
    def is_enabled(self) -> bool:
        """Check if LangSmith is enabled and properly configured"""
        return (
            self.client is not None and 
            (os.getenv('LANGCHAIN_API_KEY') is not None or os.getenv('LANGSMITH_API_KEY') is not None) and
            self.config.get('enabled', True)
        )
    
    def trace_function(self, name: Optional[str] = None, tags: Optional[list] = None):
        """Decorator to trace function execution with LangSmith. Only function-level tracing is supported."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.is_enabled():
                    return func(*args, **kwargs)
                
                try:
                    import langsmith
                    
                    # Create trace name
                    trace_name = name or f"{func.__module__}.{func.__name__}"
                    
                    # Add default tags
                    default_tags = self.config.get('tags', [])
                    all_tags = (tags or []) + default_tags
                    
                    # Start trace (function-level only)
                    try:
                        with langsmith.trace(
                            name=trace_name,
                            tags=all_tags,
                            metadata={
                                **self.config.get('metadata', {}),
                                'function': func.__name__,
                                'module': func.__module__,
                                'timestamp': datetime.now().isoformat()
                            }
                        ):
                            # Execute function; LangSmith will capture inputs/outputs automatically
                            return func(*args, **kwargs)
                    except TypeError as e:
                        if "missing 1 required positional argument: 'run_type'" in str(e):
                            # Fallback for older LangSmith versions
                            logger.warning(f"LangSmith version compatibility issue, skipping trace for {func.__name__}")
                            return func(*args, **kwargs)
                        else:
                            raise
                except Exception as e:
                    logger.warning(f"LangSmith tracing failed for {func.__name__}: {e}")
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def log_agent_execution(self, agent_name: str, task_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """
        Log agent execution to LangSmith. (No-op: child run logging is not supported in the current SDK.)
        This function is kept for API compatibility and future extension.
        """
        if not self.is_enabled():
            return
        # Function-level tracing is handled by @trace_function. No child logging here.
        pass
    
    def log_tool_execution(self, tool_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """
        Log tool execution to LangSmith. (No-op: child run logging is not supported in the current SDK.)
        This function is kept for API compatibility and future extension.
        """
        if not self.is_enabled():
            return
        # Function-level tracing is handled by @trace_function. No child logging here.
        pass

# Global LangSmith manager instance
langsmith_manager = LangSmithManager()

# Convenience functions
def trace_function(name: Optional[str] = None, tags: Optional[list] = None):
    """Convenience decorator for tracing functions"""
    return langsmith_manager.trace_function(name, tags)

def log_agent_execution(agent_name: str, task_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any]):
    """Convenience function for logging agent execution (no-op)"""
    langsmith_manager.log_agent_execution(agent_name, task_name, inputs, outputs)

def log_tool_execution(tool_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any]):
    """Convenience function for logging tool execution (no-op)"""
    langsmith_manager.log_tool_execution(tool_name, inputs, outputs) 