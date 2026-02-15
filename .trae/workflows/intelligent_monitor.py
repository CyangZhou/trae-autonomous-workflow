#!/usr/bin/env python3
"""
智能监控模块 v1.0
用于监控系统资源和触发自动化任务
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentMonitor:
    """智能监控器"""
    
    def __init__(self, config_path: str = ".trae/config/monitor.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.metrics_history: List[Dict] = []
        
    def _load_config(self) -> Dict:
        """加载配置"""
        default_config = {
            "check_interval": 60,
            "thresholds": {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90
            },
            "alerts": {
                "enabled": True,
                "channels": ["log"]
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
                
        return default_config
    
    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        try:
            import psutil
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
            }
        except ImportError:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "note": "psutil未安装，无法获取真实数据"
            }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def check_thresholds(self, metrics: Dict) -> List[Dict]:
        """检查阈值"""
        alerts = []
        thresholds = self.config.get("thresholds", {})
        
        for key, threshold in thresholds.items():
            value = metrics.get(key, 0)
            if value > threshold:
                alerts.append({
                    "type": key,
                    "value": value,
                    "threshold": threshold,
                    "severity": "warning" if value < threshold * 1.1 else "critical"
                })
        
        return alerts
    
    def run_monitoring_cycle(self) -> Dict:
        """运行监控周期"""
        metrics = self.check_system_resources()
        alerts = self.check_thresholds(metrics)
        
        result = {
            "metrics": metrics,
            "alerts": alerts,
            "status": "ok" if not alerts else "alert"
        }
        
        if alerts:
            logger.warning(f"检测到告警: {alerts}")
        
        return result
    
    def start(self, duration: int = 0):
        """启动监控"""
        logger.info("启动智能监控...")
        start_time = time.time()
        
        while True:
            self.run_monitoring_cycle()
            
            if duration > 0 and (time.time() - start_time) > duration:
                break
                
            time.sleep(self.config.get("check_interval", 60))
        
        logger.info("监控结束")


if __name__ == "__main__":
    monitor = IntelligentMonitor()
    monitor.start(duration=60)