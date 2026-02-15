"""
智能分析引擎 v4.1
5场景决策树 + 增强复杂度计算 + Skill发现集成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from .scenario_selector import ScenarioSelector, ScenarioType
from .skill_discovery import SkillDiscovery


class IntelligentAssistant:
    """
    智能分析引擎 v4.1
    
    新增功能:
    - 5场景决策树
    - 增强复杂度计算
    - Skill自动发现
    - 用户确认节点
    """
    
    def __init__(self):
        self.scenario_selector = ScenarioSelector()
        self.skill_discovery = SkillDiscovery()
        
        self._load_patterns()
    
    def _load_patterns(self):
        self.task_patterns = {
            'web_development': {
                'keywords': ['网页', '网站', '前端', 'html', 'css', 'javascript', 'react', 'vue', '页面', 'ui'],
                'complexity_base': 4,
                'typical_steps': 3
            },
            'api_development': {
                'keywords': ['api', '接口', '后端', '服务端', 'rest', 'graphql', '微服务'],
                'complexity_base': 5,
                'typical_steps': 4
            },
            'data_analysis': {
                'keywords': ['数据分析', '可视化', '报表', '统计', '爬虫', 'etl', 'excel'],
                'complexity_base': 5,
                'typical_steps': 4
            },
            'automation': {
                'keywords': ['自动化', '脚本', '批量', '定时', '工作流', '批处理'],
                'complexity_base': 4,
                'typical_steps': 3
            },
            'content_creation': {
                'keywords': ['小说', '故事', '写作', '大纲', '人物', '世界观', '文章', '公众号', '博客'],
                'complexity_base': 4,
                'typical_steps': 3
            },
            'documentation': {
                'keywords': ['文档', '飞书', 'pdf', '知识库', 'wiki', 'readme'],
                'complexity_base': 3,
                'typical_steps': 2
            }
        }
    
    def analyze(self, task_description: str, project_root: str = '.', preferred_agents: List[str] = None) -> Dict[str, Any]:
        task_lower = task_description.lower()
        task_type = self._identify_task_type(task_lower)
        
        complexity = self._calculate_complexity_enhanced(task_description, task_type)
        
        skill_result = self.skill_discovery.discover(task_description, task_type)
        has_matching_skill = skill_result.best_match is not None and skill_result.best_match.source.value != 'fallback'
        
        scenario = self.scenario_selector.select(complexity, task_description, has_matching_skill)
        
        execution_mode = 'swarm' if complexity >= 6 else 'single_agent'
        
        result = {
            'execution_mode': execution_mode,
            'complexity_score': complexity,
            'task_type': task_type,
            'scenario': scenario.scenario_type.value,
            'scenario_name': scenario.name,
            'scenario_info': {
                'name': scenario.name,
                'description': scenario.description,
                'requires_confirmation': scenario.requires_confirmation,
                'max_agents': scenario.max_agents,
                'estimated_steps': scenario.estimated_steps
            },
            'requires_confirmation': scenario.requires_confirmation,
            'skill_discovery': {
                'best_match': skill_result.best_match.name if skill_result.best_match else None,
                'source': skill_result.best_match.source.value if skill_result.best_match else None
            },
            'recommended_skills': [skill_result.best_match.name] if skill_result.best_match else [],
            'confidence': 0.8
        }
        
        return result
    
    def _identify_task_type(self, task_lower: str) -> str:
        for task_type, pattern in self.task_patterns.items():
            for keyword in pattern['keywords']:
                if keyword in task_lower:
                    return task_type
        return 'general'
    
    def _calculate_complexity_enhanced(self, task: str, task_type: str) -> int:
        base = self.task_patterns.get(task_type, {}).get('complexity_base', 3)
        modifiers = 0
        
        step_indicators = ['然后', '接着', '再', '之后', '最后', '第一步', '第二步', '第三步']
        step_count = sum(1 for ind in step_indicators if ind in task)
        if step_count >= 1: modifiers += 1
        if step_count >= 3: modifiers += 1
        
        if '集成' in task or '整合' in task: modifiers += 1
        if '多' in task and ('模块' in task or '功能' in task): modifiers += 2
        if '从零' in task or '从0' in task or '完整' in task: modifiers += 2
        
        if len(task) > 100: modifiers += 1
        if len(task) > 200: modifiers += 1
        
        return min(10, max(1, int(base + modifiers)))
    
    def get_scenario_for_task(self, task_description: str) -> Dict[str, Any]:
        task_type = self._identify_task_type(task_description.lower())
        complexity = self._calculate_complexity_enhanced(task_description, task_type)
        skill_result = self.skill_discovery.discover(task_description, task_type)
        has_skill = skill_result.best_match is not None
        
        scenario = self.scenario_selector.select(complexity, task_description, has_skill)
        
        return {
            'task_type': task_type,
            'complexity': complexity,
            'scenario': scenario.scenario_type.value,
            'scenario_name': scenario.name,
            'requires_confirmation': scenario.requires_confirmation,
            'best_skill': skill_result.best_match.name if skill_result.best_match else None
        }
