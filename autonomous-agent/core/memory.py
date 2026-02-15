"""
Memory 笔记系统 v1.3
支持会话记忆、错误记录、知识沉淀
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class MemoryType(Enum):
    SESSION = "sessions"
    TASK = "tasks"
    ERROR = "errors"
    GLOBAL = "global"


class WriteTrigger(Enum):
    TASK_START = "task_start"
    KEY_DECISION = "key_decision"
    ERROR_OCCURRED = "error_occurred"
    ERROR_FIXED = "error_fixed"
    TASK_COMPLETE = "task_complete"


class ReadTrigger(Enum):
    TASK_START = "task_start"
    ERROR_ENCOUNTERED = "error_encountered"
    SIMILAR_TASK = "similar_task"


class MemoryManager:
    """
    记忆管理器
    
    支持写入和读取:
    - 会话记忆
    - 错误修复记录
    - 任务完成经验
    """
    
    def __init__(self, memory_dir: str = None):
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            self.memory_dir = Path('.trae/memory')
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def write_note(self, trigger: WriteTrigger, content: str, context: Dict[str, Any] = None) -> Optional[str]:
        context = context or {}
        note_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        note_path = self.memory_dir / trigger.value / f"{note_id}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(note_path, 'a', encoding='utf-8') as f:
            f.write(f"# [{datetime.now().isoformat()}] {trigger.value}\n\n{content}\n")
        
        return note_id
    
    def read_note(self, note_id: str, mem_type: MemoryType = None) -> Optional[str]:
        for mt in MemoryType:
            note_path = self.memory_dir / mt.value / f"{note_id}.md"
            if note_path.exists():
                with open(note_path, 'r', encoding='utf-8') as f:
                    return f.read()
        return None
    
    def get_error_fix(self, error_message: str) -> Optional[Dict[str, str]]:
        error_sig = hashlib.md5(error_message.encode()).hexdigest()[:8]
        content = self.read_note(error_sig, MemoryType.ERROR)
        if content:
            return {'error_signature': error_sig, 'full_note': content}
        return None
    
    def record_error_and_fix(self, error_message: str, fix: str, context: Dict[str, Any] = None):
        self.write_note(WriteTrigger.ERROR_OCCURRED, f"## 错误信息\n```\n{error_message}\n```\n", context)
        self.write_note(WriteTrigger.ERROR_FIXED, f"## 修复方案\n{fix}\n", context)
