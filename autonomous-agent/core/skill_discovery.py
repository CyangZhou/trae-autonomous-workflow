"""
Skill Discovery v1.1 - Skill自动发现模块

回退链:
检测find-skills是否可用
    ↓ 可用
搜索匹配当前任务的Skill
    ↓ 找到
调用匹配的Skill执行
    ↓ 没找到或不可用
回退到本地已安装的Skill
    ↓ 本地也没有
使用通用流程
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


class SkillSource(Enum):
    LOCAL = "local"
    COMMUNITY = "community"
    BUILTIN = "builtin"
    FALLBACK = "fallback"


@dataclass
class SkillMatch:
    name: str
    source: SkillSource
    path: Optional[str] = None
    description: str = ""
    relevance_score: float = 0.0
    trigger_keywords: List[str] = field(default_factory=list)


@dataclass
class DiscoveryResult:
    task_description: str
    task_type: str
    best_match: Optional[SkillMatch] = None
    all_matches: List[SkillMatch] = field(default_factory=list)
    fallback_used: bool = False
    recommendations: List[str] = field(default_factory=list)


class SkillDiscovery:
    """
    Skill自动发现器
    
    支持三种来源:
    1. 本地已安装的Skill
    2. 内置Agent映射
    3. 通用流程回退
    """
    
    TASK_TYPE_SKILL_MAPPING = {
        'web_development': {
            'skills': ['static-webpage-dev', 'neuro-bridge'],
            'agents': ['search', 'frontend-implementation-expert'],
            'keywords': ['网页', '网站', '前端', 'html', 'css', 'react', 'vue']
        },
        'api_development': {
            'skills': ['neuro-bridge', 'duckduckgo-search'],
            'agents': ['architect-design-expert', 'backend-architect'],
            'keywords': ['api', '接口', '后端', '服务端', 'rest']
        },
        'data_analysis': {
            'skills': ['duckduckgo-search', 'ai-pdf-builder'],
            'agents': ['search', 'backend-architect'],
            'keywords': ['数据分析', '可视化', '报表', '统计']
        },
        'automation': {
            'skills': ['autonomous-agent', 'neuro-bridge'],
            'agents': ['search', 'backend-architect'],
            'keywords': ['自动化', '脚本', '批量', '工作流']
        },
        'content_creation': {
            'skills': ['novel-automation', 'priest-style-architect'],
            'agents': ['priest-style-architect', 'prompt-crafter'],
            'keywords': ['小说', '故事', '写作', '大纲', '文章']
        },
        'documentation': {
            'skills': ['feishu-doc-master', 'ai-pdf-builder'],
            'agents': ['search', 'frontend-implementation-expert'],
            'keywords': ['文档', '飞书', 'pdf', '知识库', 'readme']
        }
    }
    
    BUILTIN_AGENTS = {
        'search': {'name': 'Researcher', 'description': '搜索和调研智能体', 'best_for': ['搜索', '调研', '查找', '分析']},
        'architect-design-expert': {'name': 'Architect', 'description': '架构设计智能体', 'best_for': ['架构', '设计', '规划', '系统']},
        'backend-architect': {'name': 'Backend Architect', 'description': '后端架构和代码实现', 'best_for': ['后端', 'api', '服务', '代码']},
        'frontend-implementation-expert': {'name': 'Frontend Expert', 'description': '前端实现智能体', 'best_for': ['前端', '界面', 'ui', '页面']},
        'testing-validation-expert': {'name': 'Testing Expert', 'description': '测试和验证智能体', 'best_for': ['测试', '验证', 'qa', '质量']}
    }
    
    def __init__(self, skills_dir: str = None):
        self.skills_dir = skills_dir
        self.local_skills = {}
    
    def discover(self, task_description: str, task_type: str = None) -> DiscoveryResult:
        if not task_type:
            task_type = self._infer_task_type(task_description)
        
        result = DiscoveryResult(
            task_description=task_description,
            task_type=task_type
        )
        
        agent_matches = self._match_builtin_agents(task_description)
        result.all_matches.extend(agent_matches)
        
        if result.all_matches:
            result.best_match = result.all_matches[0]
        else:
            result.best_match = self._get_fallback()
            result.fallback_used = True
        
        return result
    
    def _infer_task_type(self, task_description: str) -> str:
        task_lower = task_description.lower()
        
        for task_type, config in self.TASK_TYPE_SKILL_MAPPING.items():
            for keyword in config.get('keywords', []):
                if keyword in task_lower:
                    return task_type
        
        return 'general'
    
    def _match_builtin_agents(self, task_description: str) -> List[SkillMatch]:
        matches = []
        task_lower = task_description.lower()
        
        for agent_type, agent_info in self.BUILTIN_AGENTS.items():
            score = 0.0
            
            for keyword in agent_info.get('best_for', []):
                if keyword in task_lower:
                    score += 0.4
            
            if score > 0:
                matches.append(SkillMatch(
                    name=agent_type,
                    source=SkillSource.BUILTIN,
                    description=agent_info.get('description', ''),
                    relevance_score=min(0.9, score)
                ))
        
        return sorted(matches, key=lambda x: x.relevance_score, reverse=True)
    
    def _get_fallback(self) -> SkillMatch:
        return SkillMatch(
            name='autonomous-agent',
            source=SkillSource.FALLBACK,
            description='通用自主执行流程',
            relevance_score=0.3
        )
