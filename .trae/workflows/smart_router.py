#!/usr/bin/env python3
"""
智能路由模块 v2.0
根据任务特征自动选择最优工作流
"""

import os
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartRouter:
    """智能路由器"""
    
    def __init__(self, workflows_dir: str = ".trae/workflows"):
        self.workflows_dir = workflows_dir
        self.workflows: Dict[str, Dict] = {}
        self.trigger_index: Dict[str, List[str]] = {}
        self._load_workflows()
        
    def _load_workflows(self):
        """加载所有工作流"""
        if not os.path.exists(self.workflows_dir):
            logger.warning(f"工作流目录不存在: {self.workflows_dir}")
            return
            
        for file in os.listdir(self.workflows_dir):
            if file.endswith('.yaml') or file.endswith('.yml'):
                workflow_path = os.path.join(self.workflows_dir, file)
                self._parse_workflow(workflow_path)
        
        logger.info(f"已加载 {len(self.workflows)} 个工作流")
    
    def _parse_workflow(self, path: str):
        """解析工作流文件"""
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
                
            if workflow:
                name = workflow.get('name', os.path.basename(path))
                self.workflows[name] = workflow
                
                # 建立触发词索引
                triggers = workflow.get('triggers', [])
                for trigger in triggers:
                    trigger_lower = trigger.lower()
                    if trigger_lower not in self.trigger_index:
                        self.trigger_index[trigger_lower] = []
                    self.trigger_index[trigger_lower].append(name)
                    
        except Exception as e:
            logger.warning(f"解析工作流失败 {path}: {e}")
    
    def match_workflow(self, task: str) -> List[Tuple[str, float]]:
        """匹配工作流"""
        task_lower = task.lower()
        matches = []
        
        # 精确匹配
        for trigger, workflow_names in self.trigger_index.items():
            if trigger in task_lower:
                for name in workflow_names:
                    matches.append((name, 1.0))
        
        # 模糊匹配
        for name, workflow in self.workflows.items():
            if name.lower() in task_lower:
                if (name, 1.0) not in matches:
                    matches.append((name, 0.8))
            
            # 检查描述
            description = workflow.get('description', '').lower()
            if description:
                words = task_lower.split()
                match_count = sum(1 for w in words if w in description)
                if match_count > 0:
                    score = match_count / len(words)
                    if score > 0.3 and (name, score) not in matches:
                        matches.append((name, score * 0.6))
        
        # 去重并排序
        unique_matches = {}
        for name, score in matches:
            if name not in unique_matches or unique_matches[name] < score:
                unique_matches[name] = score
        
        return sorted(unique_matches.items(), key=lambda x: -x[1])
    
    def route(self, task: str) -> Dict[str, Any]:
        """路由任务到最佳工作流"""
        matches = self.match_workflow(task)
        
        result = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "matches": matches[:5],
            "best_match": matches[0] if matches else None,
            "confidence": matches[0][1] if matches else 0
        }
        
        if matches:
            logger.info(f"任务 '{task}' 匹配到工作流: {matches[0][0]} (置信度: {matches[0][1]:.2f})")
        else:
            logger.warning(f"任务 '{task}' 未找到匹配的工作流")
        
        return result
    
    def get_workflow(self, name: str) -> Optional[Dict]:
        """获取工作流详情"""
        return self.workflows.get(name)
    
    def list_workflows(self) -> List[str]:
        """列出所有工作流"""
        return list(self.workflows.keys())


if __name__ == "__main__":
    router = SmartRouter()
    
    # 测试路由
    test_tasks = [
        "帮我生成API文档",
        "运行安全扫描",
        "检查代码覆盖率",
        "创建README"
    ]
    
    for task in test_tasks:
        result = router.route(task)
        print(f"\n任务: {task}")
        print(f"最佳匹配: {result['best_match']}")
        print(f"置信度: {result['confidence']:.2f}")