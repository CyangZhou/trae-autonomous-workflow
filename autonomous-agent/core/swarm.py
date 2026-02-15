"""
Swarm 蜂群编排器 v2.5
支持多智能体并行执行
"""

import sqlite3
import uuid
import json
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SwarmOrchestrator:
    """
    蜂群编排器
    
    功能:
    - 创建Swarm会话
    - 管理并行子任务
    - 汇总执行结果
    """
    
    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path('.trae/swarm/swarm_core.db')
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, 
                parent_id TEXT, 
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5, 
                worker_type TEXT, 
                payload TEXT, 
                result TEXT,
                created_at DATETIME, 
                completed_at DATETIME
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS swarm_sessions (
                session_id TEXT PRIMARY KEY, 
                main_task TEXT, 
                subtask_count INTEGER,
                completed_count INTEGER DEFAULT 0, 
                status TEXT DEFAULT 'running',
                created_at DATETIME
            )
        ''')
        conn.commit()
        conn.close()
    
    def create_swarm_session(self, main_task: str, subtasks: List[Dict]) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO swarm_sessions (session_id, main_task, subtask_count, created_at) VALUES (?, ?, ?, ?)',
            (session_id, main_task, len(subtasks), now)
        )
        
        for subtask in subtasks:
            task_id = str(uuid.uuid4())
            cursor.execute(
                'INSERT INTO tasks (task_id, parent_id, status, priority, worker_type, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (task_id, session_id, TaskStatus.PENDING.value, subtask.get('priority', 5), subtask['type'], json.dumps(subtask), now)
            )
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def get_parallel_subtasks(self, session_id: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT task_id, worker_type, payload FROM tasks WHERE parent_id = ? AND status = ?',
            (session_id, TaskStatus.PENDING.value)
        )
        rows = cursor.fetchall()
        conn.close()
        
        subtasks = []
        for row in rows:
            task_id, worker_type, payload_json = row
            payload = json.loads(payload_json)
            subtasks.append({
                'task_id': task_id,
                'subagent_type': worker_type,
                'goal': payload.get('goal', ''),
                'context': payload.get('context', '')
            })
        
        return subtasks
    
    def complete_task(self, task_id: str, result: Dict[str, Any]):
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE tasks SET status = ?, result = ?, completed_at = ? WHERE task_id = ?',
            (TaskStatus.COMPLETED.value, json.dumps(result), now, task_id)
        )
        cursor.execute(
            'SELECT parent_id FROM tasks WHERE task_id = ?', (task_id,)
        )
        row = cursor.fetchone()
        if row:
            cursor.execute(
                'UPDATE swarm_sessions SET completed_count = completed_count + 1 WHERE session_id = ?',
                (row[0],)
            )
        conn.commit()
        conn.close()
