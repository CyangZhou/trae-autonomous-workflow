"""
Scenario Selector v1.1 - 5场景决策树模块

决策树:
Q1: 任务复杂度？
├── 简单(1-2步) → 场景1：提示增强
├── 中等(3-5步) → Q2: 有现成Skill可复用？
│   ├── 是 → 场景2：Skill复用
│   └── 否 → 场景3：计划+评审
└── 复杂(6+步) → Q3: 需要明确团队分工？
    ├── 是 → 场景4：Lead-Member
    └── 否 → 场景5：复合编排
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


class ScenarioType(Enum):
    PROMPT_ENHANCEMENT = "prompt_enhancement"
    SKILL_REUSE = "skill_reuse"
    PLAN_REVIEW = "plan_review"
    LEAD_MEMBER = "lead_member"
    COMPOSITE = "composite"


@dataclass
class ScenarioInfo:
    scenario_type: ScenarioType
    name: str
    description: str
    complexity_range: Tuple[int, int]
    requires_confirmation: bool = True
    max_agents: int = 1
    estimated_steps: int = 1
    best_practices: List[str] = field(default_factory=list)


class ScenarioSelector:
    """
    5场景决策树选择器
    
    场景1: 提示增强 (复杂度 1-2)
    场景2: Skill复用 (复杂度 3-5)
    场景3: 计划+评审 (复杂度 3-5)
    场景4: Lead-Member (复杂度 6-10)
    场景5: 复合编排 (复杂度 6-10)
    """
    
    SCENARIOS = {
        ScenarioType.PROMPT_ENHANCEMENT: ScenarioInfo(
            scenario_type=ScenarioType.PROMPT_ENHANCEMENT,
            name="提示增强",
            description="任务简单，增强提示后直接执行",
            complexity_range=(1, 2),
            requires_confirmation=False,
            max_agents=1,
            estimated_steps=1
        ),
        ScenarioType.SKILL_REUSE: ScenarioInfo(
            scenario_type=ScenarioType.SKILL_REUSE,
            name="Skill复用",
            description="有现成Skill可用，直接调用执行",
            complexity_range=(3, 5),
            requires_confirmation=False,
            max_agents=1,
            estimated_steps=2
        ),
        ScenarioType.PLAN_REVIEW: ScenarioInfo(
            scenario_type=ScenarioType.PLAN_REVIEW,
            name="计划+评审",
            description="出计划→确认→执行→Review",
            complexity_range=(3, 5),
            requires_confirmation=False,
            max_agents=3,
            estimated_steps=4
        ),
        ScenarioType.LEAD_MEMBER: ScenarioInfo(
            scenario_type=ScenarioType.LEAD_MEMBER,
            name="Lead-Member",
            description="Leader协调，Member并行执行",
            complexity_range=(6, 10),
            requires_confirmation=True,
            max_agents=5,
            estimated_steps=5
        ),
        ScenarioType.COMPOSITE: ScenarioInfo(
            scenario_type=ScenarioType.COMPOSITE,
            name="复合编排",
            description="动态组合多种场景",
            complexity_range=(6, 10),
            requires_confirmation=True,
            max_agents=10,
            estimated_steps=7
        )
    }
    
    def select(self, complexity: int, task_description: str, 
               has_matching_skill: bool = None) -> ScenarioInfo:
        if complexity <= 2:
            return self.SCENARIOS[ScenarioType.PROMPT_ENHANCEMENT]
        elif complexity <= 5:
            if has_matching_skill:
                return self.SCENARIOS[ScenarioType.SKILL_REUSE]
            else:
                return self.SCENARIOS[ScenarioType.PLAN_REVIEW]
        else:
            return self.SCENARIOS[ScenarioType.LEAD_MEMBER]
    
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> ScenarioInfo:
        return self.SCENARIOS.get(scenario_type)
    
    def get_all_scenarios(self) -> Dict[ScenarioType, ScenarioInfo]:
        return self.SCENARIOS
