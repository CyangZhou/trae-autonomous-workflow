"""
Token 计量模块 v2.0
支持Token估算和使用统计
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from threading import Lock
import re


def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """
    估算文本的token数量
    
    启发式估算:
    - 英文: 约4字符 = 1 token
    - 中文: 约2字符 = 1 token
    """
    if not text:
        return 0
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(text) - chinese_chars
    
    estimated = int(chinese_chars / 1.5 + english_chars / 4)
    return max(1, estimated)


def estimate_tokens_for_dict(data: Dict, model: str = "gpt-4") -> int:
    """估算字典数据的token数量"""
    text = json.dumps(data, ensure_ascii=False)
    return estimate_tokens(text, model)


@dataclass
class TokenUsage:
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    task_type: str = "general"
    session_id: str = ""


class TokenTracker:
    _instance = None
    _lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, tracker_dir: str = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        if tracker_dir:
            self.tracker_dir = Path(tracker_dir)
        else:
            self.tracker_dir = Path('.trae/memory')
        
        self.tracker_file = self.tracker_dir / 'token_usage.json'
        self._initialized = True
        self._ensure_file()
    
    def _ensure_file(self):
        if not self.tracker_file.exists():
            self._save({
                'records': [], 
                'summary': {
                    'total_input': 0, 
                    'total_output': 0, 
                    'total_tokens': 0, 
                    'call_count': 0
                }
            })
    
    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'records': [], 'summary': {'total_input': 0, 'total_output': 0, 'total_tokens': 0, 'call_count': 0}}
    
    def _save(self, data: Dict[str, Any]):
        self.tracker_dir.mkdir(parents=True, exist_ok=True)
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def record(self, model: str, input_tokens: int, output_tokens: int, 
               task_type: str = "general", session_id: str = "") -> Dict[str, Any]:
        usage = TokenUsage(
            timestamp=datetime.now().isoformat(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            task_type=task_type,
            session_id=session_id
        )
        
        with self._lock:
            data = self._load()
            data['records'].append(asdict(usage))
            
            if len(data['records']) > 1000:
                data['records'] = data['records'][-500:]
            
            data['summary']['total_input'] += input_tokens
            data['summary']['total_output'] += output_tokens
            data['summary']['total_tokens'] += usage.total_tokens
            data['summary']['call_count'] += 1
            
            self._save(data)
        
        return {'recorded': True, 'total_tokens': usage.total_tokens}
    
    def get_summary(self) -> Dict[str, Any]:
        data = self._load()
        summary = data.get('summary', {})
        summary['avg_tokens_per_call'] = (
            summary['total_tokens'] / summary['call_count'] 
            if summary.get('call_count', 0) > 0 else 0
        )
        return summary


_tracker: Optional[TokenTracker] = None


def get_tracker() -> TokenTracker:
    global _tracker
    if _tracker is None:
        _tracker = TokenTracker()
    return _tracker


def record_usage(model: str, input_tokens: int, output_tokens: int, 
                 task_type: str = "general", session_id: str = "") -> Dict[str, Any]:
    return get_tracker().record(model, input_tokens, output_tokens, task_type, session_id)


def get_usage_summary() -> Dict[str, Any]:
    return get_tracker().get_summary()


def record_session_tokens(session_id: str, input_text: str, output_text: str, 
                          task_type: str = "general", model: str = "gpt-4") -> Dict[str, Any]:
    input_tokens = estimate_tokens(input_text, model)
    output_tokens = estimate_tokens(output_text, model)
    return record_usage(model, input_tokens, output_tokens, task_type, session_id)
