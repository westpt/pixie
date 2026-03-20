"""
核心业务逻辑层
提供 CLI 和 Web 共用的业务逻辑接口
"""

from .agent_manager import AgentManager
from .task_manager import TaskManager
from .interfaces import IAgentManager, ITaskManager

__all__ = [
    'AgentManager',
    'TaskManager',
    'IAgentManager',
    'ITaskManager'
]
