"""
Reflexion 核心模块 v2.3
错误反思与自动修复
"""

from typing import Dict, Any, Optional, List
from .memory import MemoryManager, WriteTrigger, ReadTrigger


class ReflexionCore:
    """
    反思模块
    
    功能:
    - 错误分析
    - 查询历史修复方案
    - 记录新的修复经验
    """
    
    def __init__(self, memory_dir: str = None):
        self.memory = MemoryManager(memory_dir)
    
    def reflect(self, error_log: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        反思错误，尝试找到修复方案
        
        返回:
        - action: apply_known_fix | analyze
        - fix: 修复方案
        - source: memory | inference
        """
        fix = self.memory.get_error_fix(error_log)
        
        if fix:
            return {
                'action': 'apply_known_fix',
                'fix': fix.get('fix', ''),
                'error_signature': fix.get('error_signature', ''),
                'source': 'memory'
            }
        
        return {
            'action': 'analyze',
            'fix': '需要分析错误并生成修复方案',
            'source': 'inference'
        }
    
    def record_fix(self, error_message: str, fix_solution: str, context: Dict[str, Any] = None):
        """记录错误修复方案"""
        self.memory.record_error_and_fix(error_message, fix_solution, context)
    
    def record_decision(self, decision: str, reason: str, session_id: str = None, task_type: str = None):
        """记录关键决策"""
        content = f"## 决策\n{decision}\n\n## 原因\n{reason}\n"
        self.memory.write_note(
            WriteTrigger.KEY_DECISION, 
            content, 
            {'session_id': session_id, 'task_type': task_type}
        )
