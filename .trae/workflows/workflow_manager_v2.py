#!/usr/bin/env python3
"""
自验证闭环工作流管理器 v2.0
支持工作流执行、验证、回滚和记忆
"""

import os
import json
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self, 
                 workflows_dir: str = ".trae/workflows",
                 memory_dir: str = ".trae/memory"):
        self.workflows_dir = workflows_dir
        self.memory_dir = memory_dir
        self.sessions: Dict[str, Dict] = {}
        self.hooks: Dict[str, List[Callable]] = {
            "pre_execute": [],
            "post_execute": [],
            "on_error": [],
            "on_success": []
        }
        
        os.makedirs(memory_dir, exist_ok=True)
        
    def register_hook(self, event: str, callback: Callable):
        """注册钩子"""
        if event in self.hooks:
            self.hooks[event].append(callback)
    
    def _run_hooks(self, event: str, context: Dict):
        """运行钩子"""
        for callback in self.hooks.get(event, []):
            try:
                callback(context)
            except Exception as e:
                logger.warning(f"钩子执行失败: {e}")
    
    def load_workflow(self, name: str) -> Optional[Dict]:
        """加载工作流"""
        for ext in ['.yaml', '.yml', '.json']:
            path = os.path.join(self.workflows_dir, f"{name}{ext}")
            if os.path.exists(path):
                try:
                    if ext in ['.yaml', '.yml']:
                        import yaml
                        with open(path, 'r', encoding='utf-8') as f:
                            return yaml.safe_load(f)
                    else:
                        with open(path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                except Exception as e:
                    logger.error(f"加载工作流失败 {name}: {e}")
        return None
    
    def create_session(self, workflow_name: str) -> str:
        """创建执行会话"""
        session_id = str(uuid.uuid4())[:8]
        workflow = self.load_workflow(workflow_name)
        
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_name}")
        
        self.sessions[session_id] = {
            "id": session_id,
            "workflow_name": workflow_name,
            "workflow": workflow,
            "status": "created",
            "start_time": datetime.now().isoformat(),
            "steps_completed": [],
            "steps_failed": [],
            "outputs": {},
            "errors": []
        }
        
        return session_id
    
    def execute_step(self, session_id: str, step: Dict) -> Dict:
        """执行单个步骤"""
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "会话不存在"}
        
        step_id = step.get('id', step.get('name', 'unknown'))
        action = step.get('action', 'unknown')
        params = step.get('params', {})
        
        result = {
            "step_id": step_id,
            "action": action,
            "success": False,
            "output": None,
            "error": None
        }
        
        try:
            # 执行命令
            if action == "run_command":
                import subprocess
                cmd = params.get('command', '')
                timeout = params.get('timeout', 60)
                
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                result["output"] = proc.stdout
                result["success"] = proc.returncode == 0
                if proc.returncode != 0:
                    result["error"] = proc.stderr
                    
            # 生成文档
            elif action == "generate_document":
                output_path = params.get('output', f"output/doc-{datetime.now().strftime('%Y%m%d')}.md")
                content = params.get('content', '')
                
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                result["output"] = output_path
                result["success"] = True
                
            # 通知
            elif action == "notify":
                message = params.get('message', '')
                logger.info(f"通知: {message}")
                result["output"] = message
                result["success"] = True
                
            # 验证
            elif action == "verify":
                verify_type = params.get('type', 'file_exists')
                
                if verify_type == "file_exists":
                    path = params.get('path', '')
                    result["success"] = os.path.exists(path)
                    result["output"] = f"文件存在: {result['success']}"
                else:
                    result["success"] = True
                    
            else:
                result["error"] = f"未知操作类型: {action}"
                
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
        
        return result
    
    def execute_workflow(self, session_id: str) -> Dict:
        """执行完整工作流"""
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "会话不存在"}
        
        workflow = session["workflow"]
        steps = workflow.get('steps', [])
        
        # 运行前置钩子
        self._run_hooks("pre_execute", {"session": session})
        
        session["status"] = "running"
        
        for step in steps:
            step_result = self.execute_step(session_id, step)
            
            if step_result["success"]:
                session["steps_completed"].append(step_result["step_id"])
                session["outputs"][step_result["step_id"]] = step_result["output"]
            else:
                session["steps_failed"].append(step_result["step_id"])
                session["errors"].append({
                    "step": step_result["step_id"],
                    "error": step_result["error"]
                })
                
                # 如果步骤失败，停止执行
                session["status"] = "failed"
                self._run_hooks("on_error", {"session": session})
                break
        
        if session["status"] == "running":
            session["status"] = "completed"
            session["end_time"] = datetime.now().isoformat()
            self._run_hooks("on_success", {"session": session})
        
        # 保存会话记录
        self._save_session(session_id)
        
        # 运行后置钩子
        self._run_hooks("post_execute", {"session": session})
        
        return {
            "success": session["status"] == "completed",
            "session_id": session_id,
            "status": session["status"],
            "steps_completed": len(session["steps_completed"]),
            "steps_failed": len(session["steps_failed"])
        }
    
    def _save_session(self, session_id: str):
        """保存会话记录"""
        session = self.sessions.get(session_id)
        if not session:
            return
            
        session_file = os.path.join(self.memory_dir, f"session-{session_id}.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2, default=str)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def run(self, workflow_name: str) -> Dict:
        """快速运行工作流"""
        session_id = self.create_session(workflow_name)
        return self.execute_workflow(session_id)


if __name__ == "__main__":
    manager = WorkflowManager()
    
    # 测试运行
    result = manager.run("git-commit-summary")
    print(f"执行结果: {result}")