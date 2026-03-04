"""
Agent基础类
定义Agent的通用属性与行为
"""

import logging
import uuid
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

# Agent状态枚举
class AgentStatus:
    UNINITIALIZED = 'uninitialized'  # 未初始化
    CREATED = 'created'              # 已创建
    RUNNING = 'running'              # 运行中
    STOPPED = 'stopped'              # 已停止
    DESTROYED = 'destroyed'          # 已销毁

# 任务优先级
class TaskPriority:
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

# 任务类型
class TaskType:
    SYNC = 'sync'
    ASYNC = 'async'

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Agent基础类(抽象类)
    封装Agent的通用属性与行为
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Agent
        :param config: Agent配置字典
        """
        # 基础属性
        self.agent_id = str(uuid.uuid4())  # Agent唯一ID
        self.name = config.get('name', 'Agent')
        self.agent_type = config.get('type', 'base')
        self.config = config
        
        # 状态管理
        self._status = AgentStatus.CREATED
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 任务处理相关
        self.current_task = None  # 当前处理的任务
        self.processed_count = 0  # 已处理任务数
        self.error_count = 0  # 错误计数
        
        # 日志配置
        log_level = config.get('logging', {}).get('level', 'INFO')
        log_file = config.get('logging', {}).get('file')
        self._setup_logging(log_level, log_file)
        
        logger.info(f"Agent初始化成功：{self.name} (ID: {self.agent_id})")
    
    def _setup_logging(self, level: str, log_file: Optional[str] = None):
        """
        配置日志
        :param level: 日志级别
        :param log_file: 日志文件路径
        """
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 配置处理器
        handlers = []
        if log_file:
            from pathlib import Path
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, level.upper()))
            handlers.append(file_handler)
        
        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper()))
        handlers.append(console_handler)
        
        # 配置logger
        agent_logger = logging.getLogger(f"agent.{self.name}")
        agent_logger.setLevel(logging.DEBUG)
        for handler in handlers:
            agent_logger.addHandler(handler)
        
        self.logger = agent_logger
    
    @abstractmethod
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务(抽象方法，子类必须实现)
        :param task: 任务字典，包含task_id、content、task_type等
        :return: 处理结果字典，包含content、format、execution_time、status
        """
        pass
    
    def start(self) -> bool:
        """
        启动Agent
        :return: 是否成功
        """
        if self._status == AgentStatus.RUNNING:
            self.logger.warning(f"Agent已在运行中：{self.name}")
            return False
        
        try:
            self._on_start()
            self._status = AgentStatus.RUNNING
            self.updated_at = datetime.now()
            self.logger.info(f"Agent启动成功：{self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Agent启动失败：{str(e)}")
            return False
    
    def stop(self) -> bool:
        """
        停止Agent
        :return: 是否成功
        """
        if self._status == AgentStatus.STOPPED:
            self.logger.warning(f"Agent已停止：{self.name}")
            return False
        
        try:
            self._on_stop()
            self._status = AgentStatus.STOPPED
            self.updated_at = datetime.now()
            self.logger.info(f"Agent停止成功：{self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Agent停止失败：{str(e)}")
            return False
    
    def restart(self) -> bool:
        """
        重启Agent
        :return: 是否成功
        """
        self.logger.info(f"重启Agent：{self.name}")
        self.stop()
        return self.start()
    
    def destroy(self) -> bool:
        """
        销毁Agent
        :return: 是否成功
        """
        if self._status == AgentStatus.DESTROYED:
            self.logger.warning(f"Agent已销毁：{self.name}")
            return False
        
        try:
            self._on_destroy()
            self._status = AgentStatus.DESTROYED
            self.updated_at = datetime.now()
            self.logger.info(f"Agent销毁成功：{self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Agent销毁失败：{str(e)}")
            return False
    
    def get_status(self) -> str:
        """
        获取Agent状态
        :return: 状态字符串
        """
        return self._status
    
    def validate_state(self, target_state: str) -> bool:
        """
        验证状态转换是否合法
        :param target_state: 目标状态
        :return: 是否合法
        """
        # 状态转换规则
        state_transitions = {
            AgentStatus.UNINITIALIZED: [AgentStatus.CREATED],
            AgentStatus.CREATED: [AgentStatus.RUNNING, AgentStatus.DESTROYED],
            AgentStatus.RUNNING: [AgentStatus.STOPPED, AgentStatus.DESTROYED],
            AgentStatus.STOPPED: [AgentStatus.RUNNING, AgentStatus.DESTROYED],
            AgentStatus.DESTROYED: []  # 销毁后不能转换到其他状态
        }
        
        allowed_transitions = state_transitions.get(self._status, [])
        return target_state in allowed_transitions
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取Agent信息
        :return: Agent信息字典
        """
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'type': self.agent_type,
            'status': self._status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'current_task': self.current_task
        }
    
    def _on_start(self):
        """
        Agent启动时的回调(子类可覆盖)
        """
        pass
    
    def _on_stop(self):
        """
        Agent停止时的回调(子类可覆盖)
        """
        pass
    
    def _on_destroy(self):
        """
        Agent销毁时的回调(子类可覆盖)
        """
        pass
    
    def _update_processed_count(self, success: bool = True):
        """
        更新处理计数
        :param success: 是否成功
        """
        self.processed_count += 1
        if not success:
            self.error_count += 1
        
        self.updated_at = datetime.now()
