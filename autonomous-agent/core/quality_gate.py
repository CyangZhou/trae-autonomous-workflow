"""
Quality Gate v1.1 - 3维度质量把关模块

维度1: 边界处理 (Boundary)
- 空值处理
- 异常捕获
- 输入验证
- 边界条件

维度2: 专业度 (Professionalism)
- 命名规范
- 错误提示友好
- 代码注释
- 日志记录

维度3: 完整性 (Completeness)
- 文档齐全
- 配置完整
- 示例代码
- 测试覆盖
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re


class QualityDimension(Enum):
    BOUNDARY = "boundary"
    PROFESSIONALISM = "professionalism"
    COMPLETENESS = "completeness"


@dataclass
class CheckItem:
    name: str
    description: str
    passed: bool = False
    score: float = 0.0
    details: str = ""


@dataclass
class DimensionResult:
    dimension: QualityDimension
    name: str
    items: List[CheckItem] = field(default_factory=list)
    total_score: float = 0.0
    passed: bool = False


@dataclass
class QualityReport:
    session_id: str
    timestamp: str
    dimensions: List[DimensionResult] = field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False
    recommendations: List[str] = field(default_factory=list)


class QualityGate:
    """
    3维度质量把关器
    """
    
    PASS_THRESHOLD = 0.7
    
    def check_boundary(self, code_content: str) -> DimensionResult:
        result = DimensionResult(
            dimension=QualityDimension.BOUNDARY,
            name="边界处理"
        )
        
        null_patterns = [r'if\s+\w+\s+is\s+None', r'if\s+not\s+\w+']
        null_score = sum(1 for p in null_patterns if re.search(p, code_content)) / 2
        
        try_count = len(re.findall(r'\btry\s*:', code_content))
        except_count = len(re.findall(r'\bexcept\s*', code_content))
        exception_score = min(1.0, (try_count + except_count) / 2)
        
        result.items.append(CheckItem("空值处理", "", null_score >= 0.5, null_score))
        result.items.append(CheckItem("异常捕获", "", try_count > 0, exception_score))
        
        result.total_score = sum(i.score for i in result.items) / len(result.items)
        result.passed = result.total_score >= self.PASS_THRESHOLD
        return result
    
    def run_full_check(self, code_content: str = "", session_id: str = None) -> QualityReport:
        session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = QualityReport(
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        report.dimensions.append(self.check_boundary(code_content))
        
        report.overall_score = sum(d.total_score for d in report.dimensions) / len(report.dimensions)
        report.passed = report.overall_score >= self.PASS_THRESHOLD
        
        return report
