"""
核心业务接口定义
定义 CLI 和 Web 共用的业务逻辑接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class IAgentManager(ABC):
    """Agent 管理接口"""

    @abstractmethod
    def register_agent(self, config: Dict[str, Any]) -> str:
        """
        注册新 Agent
        :param config: Agent 配置
        :return: Agent ID
        """
        pass

    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 信息
        :param agent_id: Agent ID
        :return: Agent 信息
        """
        pass

    @abstractmethod
    def list_agents(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        列出所有 Agent
        :param filters: 过滤条件
        :return: Agent 列表
        """
        pass

    @abstractmethod
    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新 Agent 信息
        :param agent_id: Agent ID
        :param updates: 更新内容
        :return: 是否成功
        """
        pass

    @abstractmethod
    def delete_agent(self, agent_id: str) -> bool:
        """
        删除 Agent
        :param agent_id: Agent ID
        :return: 是否成功
        """
        pass

    @abstractmethod
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 状态
        :param agent_id: Agent ID
        :return: 状态信息
        """
        pass


class ITaskManager(ABC):
    """任务管理接口"""

    @abstractmethod
    def create_task(self, content: str, task_type: str = 'sync', priority: str = 'medium') -> str:
        """
        创建任务
        :param content: 任务内容
        :param task_type: 任务类型
        :param priority: 优先级
        :return: 任务 ID
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        :param task_id: 任务 ID
        :return: 任务信息
        """
        pass

    @abstractmethod
    def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        列出所有任务
        :param filters: 过滤条件
        :return: 任务列表
        """
        pass

    @abstractmethod
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        更新任务状态
        :param task_id: 任务 ID
        :param status: 新状态
        :return: 是否成功
        """
        pass

    @abstractmethod
    def execute_task(self, task_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行任务
        :param task_id: 任务 ID
        :param agent_id: Agent ID（可选）
        :return: 执行结果
        """
        pass


class IDataAccess(ABC):
    """数据访问接口"""

    @abstractmethod
    def query(self, query: str, params: tuple = ()) -> Any:
        """
        执行查询
        :param query: SQL 查询
        :param params: 参数
        :return: 查询结果
        """
        pass

    @abstractmethod
    def execute(self, query: str, params: tuple = ()) -> int:
        """
        执行更新
        :param query: SQL 语句
        :param params: 参数
        :return: 影响行数
        """
        pass
