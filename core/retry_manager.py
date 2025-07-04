#!/usr/bin/env python3
"""
Retry and Recovery Manager for Patent Automation System
Handles tool failures, retries, and recovery mechanisms
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

logger = logging.getLogger(__name__)

class RetryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY_EXHAUSTED = "retry_exhausted"
    SKIPPED = "skipped"

@dataclass
class RetryAttempt:
    attempt_number: int
    timestamp: str
    error_type: str
    error_message: str
    duration: float
    success: bool

@dataclass
class ToolExecutionRecord:
    patent_id: str
    tool_name: str
    status: RetryStatus
    attempts: List[RetryAttempt]
    total_duration: float
    created_at: str
    completed_at: Optional[str]
    final_result: Optional[str]
    error_summary: Optional[str]
    retry_count: int
    max_retries: int

class RetryManager:
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 30.0,
                 backoff_factor: float = 2.0,
                 recovery_file: str = "patent_output/recovery_data.json"):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.recovery_file = Path(recovery_file)
        self.execution_records: Dict[str, ToolExecutionRecord] = {}
        self.load_recovery_data()
    
    def load_recovery_data(self):
        """Load existing recovery data from file"""
        if self.recovery_file.exists():
            try:
                with open(self.recovery_file, 'r') as f:
                    data = json.load(f)
                    for record_id, record_data in data.items():
                        # Convert back to ToolExecutionRecord
                        record_data['status'] = RetryStatus(record_data['status'])
                        record_data['attempts'] = [RetryAttempt(**attempt) for attempt in record_data['attempts']]
                        self.execution_records[record_id] = ToolExecutionRecord(**record_data)
                logger.info(f"Loaded {len(self.execution_records)} execution records from recovery file")
            except Exception as e:
                logger.warning(f"Failed to load recovery data: {e}")
    
    def save_recovery_data(self):
        """Save recovery data to file"""
        try:
            self.recovery_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.recovery_file, 'w') as f:
                # Convert records to serializable format
                data = {}
                for record_id, record in self.execution_records.items():
                    record_dict = asdict(record)
                    record_dict['status'] = record.status.value
                    data[record_id] = record_dict
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recovery data: {e}")
    
    def get_record_id(self, patent_id: str, tool_name: str) -> str:
        """Generate unique record ID"""
        return f"{patent_id}_{tool_name}"
    
    def should_retry(self, record_id: str) -> bool:
        """Check if we should retry based on current record"""
        if record_id not in self.execution_records:
            return True
        
        record = self.execution_records[record_id]
        return record.retry_count < self.max_retries and record.status not in [RetryStatus.SUCCESS, RetryStatus.SKIPPED]
    
    def get_retry_delay(self, attempt_number: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.base_delay * (self.backoff_factor ** (attempt_number - 1))
        return min(delay, self.max_delay)
    
    def execute_with_retry(self, 
                          patent_id: str, 
                          tool_name: str, 
                          tool_function: Callable, 
                          *args, 
                          **kwargs) -> str:
        """Execute a tool function with retry logic"""
        record_id = self.get_record_id(patent_id, tool_name)
        
        # Check if we should retry based on existing record
        if not self.should_retry(record_id):
            record = self.execution_records[record_id]
            if record.status == RetryStatus.SUCCESS and record.final_result:
                logger.info(f"Using cached successful result for {record_id}")
                return record.final_result
            elif record.status == RetryStatus.RETRY_EXHAUSTED:
                logger.warning(f"Retry exhausted for {record_id}, skipping")
                return f"SKIPPED: {record.error_summary}"
        
        # Create or update execution record
        if record_id not in self.execution_records:
            self.execution_records[record_id] = ToolExecutionRecord(
                patent_id=patent_id,
                tool_name=tool_name,
                status=RetryStatus.PENDING,
                attempts=[],
                total_duration=0.0,
                created_at=datetime.now().isoformat(),
                completed_at=None,
                final_result=None,
                error_summary=None,
                retry_count=0,
                max_retries=self.max_retries
            )
        
        record = self.execution_records[record_id]
        record.status = RetryStatus.IN_PROGRESS
        self.save_recovery_data()
        
        # Execute with retries
        for attempt_num in range(1, self.max_retries + 1):
            start_time = time.time()
            
            try:
                logger.info(f"Executing {tool_name} for patent {patent_id} (attempt {attempt_num}/{self.max_retries})")
                
                # Execute the tool function
                result = tool_function(*args, **kwargs)
                
                # Check if result indicates success (not an error message)
                if result and not result.startswith("ERROR IN") and not result.startswith("SKIPPED"):
                    # Success!
                    duration = time.time() - start_time
                    attempt = RetryAttempt(
                        attempt_number=attempt_num,
                        timestamp=datetime.now().isoformat(),
                        error_type="None",
                        error_message="Success",
                        duration=duration,
                        success=True
                    )
                    
                    record.attempts.append(attempt)
                    record.status = RetryStatus.SUCCESS
                    record.completed_at = datetime.now().isoformat()
                    record.final_result = result
                    record.total_duration = sum(a.duration for a in record.attempts)
                    record.retry_count = attempt_num - 1
                    
                    logger.info(f"✅ {tool_name} for patent {patent_id} completed successfully on attempt {attempt_num}")
                    self.save_recovery_data()
                    return result
                else:
                    # Tool returned error message
                    raise Exception(f"Tool returned error: {result[:200]}...")
                    
            except Exception as e:
                duration = time.time() - start_time
                error_type = type(e).__name__
                error_message = str(e)
                
                attempt = RetryAttempt(
                    attempt_number=attempt_num,
                    timestamp=datetime.now().isoformat(),
                    error_type=error_type,
                    error_message=error_message,
                    duration=duration,
                    success=False
                )
                
                record.attempts.append(attempt)
                record.retry_count = attempt_num
                
                logger.warning(f"❌ {tool_name} for patent {patent_id} failed on attempt {attempt_num}: {error_type}: {error_message}")
                
                # If this was the last attempt, mark as failed
                if attempt_num == self.max_retries:
                    record.status = RetryStatus.RETRY_EXHAUSTED
                    record.completed_at = datetime.now().isoformat()
                    record.error_summary = f"Failed after {self.max_retries} attempts. Last error: {error_type}: {error_message}"
                    record.total_duration = sum(a.duration for a in record.attempts)
                    
                    logger.error(f"💥 {tool_name} for patent {patent_id} failed after {self.max_retries} attempts")
                    self.save_recovery_data()
                    
                    # Return a fallback result
                    return self._generate_fallback_result(tool_name, patent_id, error_message)
                
                # Wait before retry
                delay = self.get_retry_delay(attempt_num)
                logger.info(f"⏳ Waiting {delay:.1f}s before retry {attempt_num + 1}")
                time.sleep(delay)
        
        # Should never reach here, but just in case
        return f"UNEXPECTED_ERROR: {tool_name} for patent {patent_id}"
    
    def _generate_fallback_result(self, tool_name: str, patent_id: str, error_message: str) -> str:
        """Generate a fallback result when tool fails completely"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        fallback_templates = {
            "real_patent_search_tool": f"""
FALLBACK PRIOR ART SEARCH REPORT
================================

Patent ID: {patent_id}
Tool: {tool_name}
Status: FAILED - Using fallback analysis
Timestamp: {timestamp}
Error: {error_message}

FALLBACK ANALYSIS:
Due to technical issues with the patent search tool, this analysis is based on general 
knowledge of the patent landscape for this technology area.

RECOMMENDATIONS:
1. Manual prior art search recommended
2. Consider consulting with patent attorney
3. Review similar patents in the field
4. Conduct keyword-based search on USPTO/EPO

NEXT STEPS:
- Perform manual patent search
- Review academic literature
- Consult with patent professionals
- Consider filing with provisional application

This fallback analysis should not be used as the sole basis for patent filing decisions.
""",
            "arxiv_search_tool": f"""
FALLBACK ACADEMIC LITERATURE ANALYSIS
=====================================

Patent ID: {patent_id}
Tool: {tool_name}
Status: FAILED - Using fallback analysis
Timestamp: {timestamp}
Error: {error_message}

FALLBACK ANALYSIS:
Due to technical issues with the academic search tool, this analysis is based on general 
knowledge of the academic landscape for this technology area.

RECOMMENDATIONS:
1. Manual academic literature search recommended
2. Review recent papers in related fields
3. Check IEEE, ACM, and other academic databases
4. Consult with academic experts in the field

NEXT STEPS:
- Perform manual academic search
- Review recent publications
- Check conference proceedings
- Consult with academic experts

This fallback analysis should not be used as the sole basis for patent filing decisions.
""",
            "vector_based_overlap_analysis_tool": f"""
FALLBACK OVERLAP ANALYSIS
=========================

Patent ID: {patent_id}
Tool: {tool_name}
Status: FAILED - Using fallback analysis
Timestamp: {timestamp}
Error: {error_message}

FALLBACK ANALYSIS:
Due to technical issues with the vector analysis tool, this analysis is based on simple 
text comparison and general knowledge.

RECOMMENDATIONS:
1. Manual overlap analysis recommended
2. Review claims for obvious similarities
3. Check for direct infringement risks
4. Consult with patent attorney for detailed analysis

NEXT STEPS:
- Perform manual overlap analysis
- Review claims carefully
- Check for obvious similarities
- Consult with patent professionals

This fallback analysis should not be used as the sole basis for patent filing decisions.
""",
            "default": f"""
FALLBACK ANALYSIS REPORT
========================

Patent ID: {patent_id}
Tool: {tool_name}
Status: FAILED - Using fallback analysis
Timestamp: {timestamp}
Error: {error_message}

FALLBACK ANALYSIS:
Due to technical issues with the {tool_name}, this analysis is incomplete.

RECOMMENDATIONS:
1. Manual analysis recommended
2. Consult with patent professionals
3. Review similar patents and literature
4. Consider filing with provisional application

NEXT STEPS:
- Perform manual analysis
- Consult with experts
- Review related work
- Consider provisional filing

This fallback analysis should not be used as the sole basis for patent filing decisions.
"""
        }
        
        return fallback_templates.get(tool_name, fallback_templates["default"])
    
    def get_failed_executions(self) -> List[ToolExecutionRecord]:
        """Get list of failed executions for recovery"""
        return [record for record in self.execution_records.values() 
                if record.status in [RetryStatus.FAILED, RetryStatus.RETRY_EXHAUSTED]]
    
    def get_pending_executions(self) -> List[ToolExecutionRecord]:
        """Get list of pending executions"""
        return [record for record in self.execution_records.values() 
                if record.status == RetryStatus.PENDING]
    
    def reset_execution(self, patent_id: str, tool_name: str):
        """Reset an execution record to allow retry"""
        record_id = self.get_record_id(patent_id, tool_name)
        if record_id in self.execution_records:
            record = self.execution_records[record_id]
            record.status = RetryStatus.PENDING
            record.retry_count = 0
            record.attempts = []
            record.completed_at = None
            record.final_result = None
            record.error_summary = None
            self.save_recovery_data()
            logger.info(f"Reset execution record for {record_id}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions"""
        total = len(self.execution_records)
        successful = len([r for r in self.execution_records.values() if r.status == RetryStatus.SUCCESS])
        failed = len([r for r in self.execution_records.values() if r.status in [RetryStatus.FAILED, RetryStatus.RETRY_EXHAUSTED]])
        pending = len([r for r in self.execution_records.values() if r.status == RetryStatus.PENDING])
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "pending": pending,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "average_retries": sum(r.retry_count for r in self.execution_records.values()) / total if total > 0 else 0
        } 