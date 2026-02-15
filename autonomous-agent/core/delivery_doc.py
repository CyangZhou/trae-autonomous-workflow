"""
Delivery Doc v1.1 - 交付文档生成模块

生成内容:
1. 部署说明
2. 验证方法
3. 限制说明
4. 后续建议
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DeploymentStep:
    order: int
    action: str
    command: str = ""
    description: str = ""


@dataclass
class VerificationMethod:
    name: str
    description: str
    steps: List[str] = field(default_factory=list)
    expected_output: str = ""


@dataclass
class DeliveryDocument:
    session_id: str
    task_description: str
    generated_at: str
    scenario_used: str = ""
    summary: str = ""
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    deployment_steps: List[DeploymentStep] = field(default_factory=list)
    verification_methods: List[VerificationMethod] = field(default_factory=list)
    quality_score: float = 0.0


class DeliveryDocGenerator:
    """
    交付文档生成器
    """
    
    DEPLOYMENT_TEMPLATES = {
        'python': [
            DeploymentStep(1, "安装依赖", "pip install -r requirements.txt", "安装项目所需的所有Python包"),
            DeploymentStep(2, "配置环境变量", "cp .env.example .env", "复制环境变量模板并配置"),
            DeploymentStep(3, "运行应用", "python main.py", "启动应用程序"),
        ],
        'general': [
            DeploymentStep(1, "检查环境", "确认运行环境满足要求", "验证系统配置"),
            DeploymentStep(2, "执行程序", "按照具体说明执行", "运行主要功能"),
        ]
    }
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path('.trae/delivery')
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, session_id: str, task_description: str, 
                 execution_result: Dict[str, Any] = None,
                 quality_report: Dict[str, Any] = None) -> DeliveryDocument:
        doc = DeliveryDocument(
            session_id=session_id,
            task_description=task_description,
            generated_at=datetime.now().isoformat()
        )
        
        if execution_result:
            doc.scenario_used = execution_result.get('scenario', 'unknown')
            doc.files_created = execution_result.get('files_created', [])
            doc.files_modified = execution_result.get('files_modified', [])
            doc.summary = self._generate_summary(execution_result)
        
        if quality_report:
            doc.quality_score = quality_report.get('overall_score', 0)
        
        doc.deployment_steps = self._generate_deployment_steps(execution_result)
        doc.verification_methods = self._generate_verification_methods()
        
        return doc
    
    def _generate_summary(self, execution_result: Dict) -> str:
        if not execution_result:
            return "任务已完成"
        
        parts = []
        if execution_result.get('files_created'):
            parts.append(f"创建了 {len(execution_result['files_created'])} 个文件")
        if execution_result.get('files_modified'):
            parts.append(f"修改了 {len(execution_result['files_modified'])} 个文件")
        
        return "，".join(parts) + "。" if parts else "任务已成功完成。"
    
    def _generate_deployment_steps(self, execution_result: Dict) -> List[DeploymentStep]:
        return self.DEPLOYMENT_TEMPLATES.get('general', [])
    
    def _generate_verification_methods(self) -> List[VerificationMethod]:
        return [
            VerificationMethod(
                name="功能验证",
                description="验证核心功能是否正常工作",
                steps=["运行主程序或测试脚本", "检查输出是否符合预期"],
                expected_output="所有功能正常，无错误输出"
            )
        ]
