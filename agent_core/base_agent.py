"""
Agent基础类
定义Agent的核心接口、状态管理和生命周期
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
import logging
import threading
import time
from datetime import datetime


class AgentState(Enum):
    """
    Agent状态枚举
    定义Agent的生命周期状态
    """
    UNINITIALIZED = "uninitialized"  # 未初始化
    CREATED = "created"              # 已创建
    RUNNING = "running"              # 运行中
    STOPPED = "stopped"              # 已停止
    DESTROYED = "destroyed"          # 已销毁

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"AgentState.{self.name}"


class AgentError(Exception):
    """Agent错误基类"""
    pass


class AgentStateError(AgentError):
    """Agent状态错误"""
    pass


class AgentNotReadyError(AgentError):
    """Agent未就绪错误"""
    pass


class BaseAgent(ABC):
    """
    Agent基础类（抽象基类）
    定义Agent的核心接口和生命周期管理
    """

    # 状态转换规则：允许的状态转换
    STATE_TRANSITIONS = {
        AgentState.UNINITIALIZED: [AgentState.CREATED],
        AgentState.CREATED: [AgentState.RUNNING, AgentState.DESTROYED],
        AgentState.RUNNING: [AgentState.STOPPED, AgentState.DESTROYED],
        AgentState.STOPPED: [AgentState.RUNNING, AgentState.DESTROYED],
        AgentState.DESTROYED: [],  # 已销毁的状态不能转换
    }

    def __init__(self, agent_id: int, name: str, agent_type: str, config: Dict[str, Any]):
        """
        初始化Agent
        :param agent_id: Agent ID（数据库ID）
        :param name: Agent名称
        :param agent_type: Agent类型
        :param config: Agent配置字典
        """
        self._agent_id = agent_id
        self._name = name
        self._type = agent_type
        self._config = config

        # 状态管理
        self._state = AgentState.UNINITIALIZED
        self._state_lock = threading.Lock()

        # 生命周期管理
        self._created_at = None
        self._started_at = None
        self._stopped_at = None
        self._destroyed_at = None

        # 任务统计
        self._total_tasks = 0
        self._successful_tasks = 0
        self._failed_tasks = 0

        # 日志
        self._logger = self._setup_logger()

        # 事件回调（用于生命周期事件通知）
        self._on_state_change_callbacks = []
        self._on_task_start_callbacks = []
        self._on_task_complete_callbacks = []
        self._on_task_error_callbacks = []

        # 错误处理
        self._error_handler = None

        self._logger.info(f"Agent初始化: {name} (ID: {agent_id}, 类型: {agent_type})")

    def _setup_logger(self) -> logging.Logger:
        """
        设置Agent专用日志记录器
        :return: 日志记录器
        """
        logger = logging.getLogger(f"agent.{self._name}.{self._agent_id}")
        logger.setLevel(logging.DEBUG)

        # 避免重复添加handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    @property
    def agent_id(self) -> int:
        """获取Agent ID"""
        return self._agent_id

    @property
    def name(self) -> str:
        """获取Agent名称"""
        return self._name

    @property
    def type(self) -> str:
        """获取Agent类型"""
        return self._type

    @property
    def config(self) -> Dict[str, Any]:
        """获取Agent配置"""
        return self._config.copy()

    @property
    def state(self) -> AgentState:
        """获取Agent状态"""
        return self._state

    @property
    def is_running(self) -> bool:
        """Agent是否运行中"""
        return self._state == AgentState.RUNNING

    @property
    def is_stopped(self) -> bool:
        """Agent是否已停止"""
        return self._state == AgentState.STOPPED

    @property
    def is_destroyed(self) -> bool:
        """Agent是否已销毁"""
        return self._state == AgentState.DESTROYED

    @property
    def task_statistics(self) -> Dict[str, int]:
        """获取任务统计"""
        return {
            'total': self._total_tasks,
            'successful': self._successful_tasks,
            'failed': self._failed_tasks,
            'success_rate': self._successful_tasks / self._total_tasks if self._total_tasks > 0 else 0.0
        }

    def _validate_state_transition(self, new_state: AgentState) -> bool:
        """
        验证状态转换是否合法
        :param new_state: 目标状态
        :return: 是否允许转换
        :raises: AgentStateError 如果转换不合法
        """
        if self._state == AgentState.DESTROYED:
            raise AgentStateError(
                f"Agent已销毁，无法进行任何状态转换（当前: {self._state} -> 目标: {new_state}）"
            )

        allowed_transitions = self.STATE_TRANSITIONS.get(self._state, [])
        if new_state not in allowed_transitions:
            raise AgentStateError(
                f"非法的状态转换: {self._state} -> {new_state}。"
                f"允许的转换: {[s.value for s in allowed_transitions]}"
            )

        return True

    def _set_state(self, new_state: AgentState):
        """
        设置Agent状态（内部方法）
        :param new_state: 新状态
        """
        with self._state_lock:
            self._validate_state_transition(new_state)
            old_state = self._state
            self._state = new_state

            # 更新时间戳
            now = datetime.now()
            if new_state == AgentState.CREATED:
                self._created_at = now
            elif new_state == AgentState.RUNNING:
                self._started_at = now
            elif new_state == AgentState.STOPPED:
                self._stopped_at = now
            elif new_state == AgentState.DESTROYED:
                self._destroyed_at = now

            # 记录日志
            self._logger.info(f"状态转换: {old_state.value} -> {new_state.value}")

            # 调用状态变化回调
            self._notify_state_change(old_state, new_state)

    def _notify_state_change(self, old_state: AgentState, new_state: AgentState):
        """
        通知状态变化
        :param old_state: 旧状态
        :param new_state: 新状态
        """
        for callback in self._on_state_change_callbacks:
            try:
                callback(self, old_state, new_state)
            except Exception as e:
                self._logger.error(f"状态变化回调失败: {str(e)}")

    def _notify_task_start(self, task: Dict[str, Any]):
        """
        通知任务开始
        :param task: 任务信息
        """
        for callback in self._on_task_start_callbacks:
            try:
                callback(self, task)
            except Exception as e:
                self._logger.error(f"任务开始回调失败: {str(e)}")

    def _notify_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]):
        """
        通知任务完成
        :param task: 任务信息
        :param result: 执行结果
        """
        for callback in self._on_task_complete_callbacks:
            try:
                callback(self, task, result)
            except Exception as e:
                self._logger.error(f"任务完成回调失败: {str(e)}")

    def _notify_task_error(self, task: Dict[str, Any], error: Exception):
        """
        通知任务错误
        :param task: 任务信息
        :param error: 错误信息
        """
        for callback in self._on_task_error_callbacks:
            try:
                callback(self, task, error)
            except Exception as e:
                self._logger.error(f"任务错误回调失败: {str(e)}")

    def register_state_change_callback(self, callback: Callable):
        """
        注册状态变化回调
        :param callback: 回调函数 (agent, old_state, new_state) -> None
        """
        self._on_state_change_callbacks.append(callback)
        self._logger.debug(f"注册状态变化回调: {callback.__name__}")

    def register_task_start_callback(self, callback: Callable):
        """
        注册任务开始回调
        :param callback: 回调函数 (agent, task) -> None
        """
        self._on_task_start_callbacks.append(callback)
        self._logger.debug(f"注册任务开始回调: {callback.__name__}")

    def register_task_complete_callback(self, callback: Callable):
        """
        注册任务完成回调
        :param callback: 回调函数 (agent, task, result) -> None
        """
        self._on_task_complete_callbacks.append(callback)
        self._logger.debug(f"注册任务完成回调: {callback.__name__}")

    def register_task_error_callback(self, callback: Callable):
        """
        注册任务错误回调
        :param callback: 回调函数 (agent, task, error) -> None
        """
        self._on_task_error_callbacks.append(callback)
        self._logger.debug(f"注册任务错误回调: {callback.__name__}")

    def set_error_handler(self, handler: Callable[[Exception, Dict[str, Any]], Optional[Dict[str, Any]]]):
        """
        设置错误处理器
        :param handler: 错误处理函数 (error, context) -> result or None
        """
        self._error_handler = handler
        self._logger.debug(f"设置错误处理器: {handler.__name__}")

    def create(self):
        """
        创建Agent（初始化）
        :raises: AgentStateError 如果状态转换不合法
        """
        self._logger.info(f"创建Agent: {self._name}")
        self._set_state(AgentState.CREATED)
        self._logger.info(f"Agent创建成功: {self._name} (ID: {self._agent_id})")

    def start(self):
        """
        启动Agent
        :raises: AgentStateError 如果状态转换不合法
        """
        self._logger.info(f"启动Agent: {self._name}")
        self._set_state(AgentState.RUNNING)
        self._logger.info(f"Agent启动成功: {self._name} (ID: {self._agent_id})")

    def stop(self):
        """
        停止Agent
        :raises: AgentStateError 如果状态转换不合法
        """
        self._logger.info(f"停止Agent: {self._name}")
        self._set_state(AgentState.STOPPED)
        self._logger.info(f"Agent已停止: {self._name} (ID: {self._agent_id})")

    def restart(self):
        """
        重启Agent
        :raises: AgentStateError 如果状态转换不合法
        """
        self._logger.info(f"重启Agent: {self._name}")
        self.stop()
        time.sleep(0.1)  # 短暂延迟确保状态转换完成
        self.start()
        self._logger.info(f"Agent重启成功: {self._name} (ID: {self._agent_id})")

    def destroy(self):
        """
        销毁Agent（清理资源）
        :raises: AgentStateError 如果状态转换不合法
        """
        self._logger.info(f"销毁Agent: {self._name}")

        # 如果正在运行，先停止
        if self._state == AgentState.RUNNING:
            self.stop()

        # 清理回调
        self._on_state_change_callbacks.clear()
        self._on_task_start_callbacks.clear()
        self._on_task_complete_callbacks.clear()
        self._on_task_error_callbacks.clear()

        # 设置为销毁状态
        self._set_state(AgentState.DESTROYED)
        self._logger.info(f"Agent已销毁: {self._name} (ID: {self._agent_id})")

    def get_status(self) -> Dict[str, Any]:
        """
        获取Agent状态信息
        :return: 状态信息字典
        """
        return {
            'agent_id': self._agent_id,
            'name': self._name,
            'type': self._type,
            'state': self._state.value,
            'is_running': self.is_running,
            'is_stopped': self.is_stopped,
            'is_destroyed': self.is_destroyed,
            'created_at': self._created_at.isoformat() if self._created_at else None,
            'started_at': self._started_at.isoformat() if self._started_at else None,
            'stopped_at': self._stopped_at.isoformat() if self._stopped_at else None,
            'destroyed_at': self._destroyed_at.isoformat() if self._destroyed_at else None,
            'task_statistics': self.task_statistics,
            'uptime': self._calculate_uptime() if self._started_at else 0
        }

    def _calculate_uptime(self) -> float:
        """
        计算Agent运行时间（秒）
        :return: 运行时间（秒）
        """
        if not self._started_at:
            return 0.0

        if self._state == AgentState.RUNNING:
            # 如果正在运行，计算从启动到现在的时长
            uptime = (datetime.now() - self._started_at).total_seconds()
        elif self._stopped_at:
            # 如果已停止，计算从启动到停止的时长
            uptime = (self._stopped_at - self._started_at).total_seconds()
        else:
            uptime = 0.0

        return uptime

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务（抽象方法，子类必须实现）
        :param task: 任务信息字典
        :return: 任务执行结果
        :raises: AgentNotReadyError 如果Agent未就绪
        :raises: Exception 处理失败
        """
        # 检查Agent是否就绪
        if self._state != AgentState.RUNNING:
            raise AgentNotReadyError(
                f"Agent未就绪，无法处理任务（当前状态: {self._state.value}）。"
                f"请先启动Agent。"
            )

        self._logger.info(f"开始处理任务: {task.get('task_id', 'unknown')}")

        # 更新任务统计
        self._total_tasks += 1

        # 通知任务开始
        self._notify_task_start(task)

        try:
            # 执行任务（子类实现）
            start_time = time.time()
            result = self._execute_task(task)
            execution_time = time.time() - start_time

            # 添加执行时间到结果
            result['execution_time'] = execution_time
            result['processed_at'] = datetime.now().isoformat()

            # 更新成功统计
            self._successful_tasks += 1

            self._logger.info(
                f"任务处理成功: {task.get('task_id', 'unknown')}, "
                f"耗时: {execution_time:.2f}秒"
            )

            # 通知任务完成
            self._notify_task_complete(task, result)

            return result

        except Exception as e:
            # 更新失败统计
            self._failed_tasks += 1

            self._logger.error(
                f"任务处理失败: {task.get('task_id', 'unknown')}, "
                f"错误: {str(e)}"
            )

            # 尝试使用错误处理器
            if self._error_handler:
                try:
                    result = self._error_handler(e, {'task': task, 'agent': self.get_status()})
                    if result:
                        self._logger.info("错误处理器返回了结果")
                        return result
                except Exception as handler_error:
                    self._logger.error(f"错误处理器失败: {str(handler_error)}")

            # 通知任务错误
            self._notify_task_error(task, e)

            # 重新抛出异常
            raise AgentError(f"任务处理失败: {str(e)}") from e

    @abstractmethod
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务（抽象方法，子类必须实现）
        :param task: 任务信息
        :return: 执行结果
        """
        pass

    def validate_config(self) -> bool:
        """
        验证Agent配置
        :return: 配置是否有效
        """
        if not self._config:
            self._logger.warning("配置为空")
            return False

        # 基本验证：必须包含name和type
        if not isinstance(self._config, dict):
            self._logger.error(f"配置类型错误: {type(self._config)}")
            return False

        return True

    def __repr__(self) -> str:
        return (
            f"BaseAgent(id={self._agent_id}, name='{self._name}', "
            f"type='{self._type}', state={self._state.value})"
        )

    def __str__(self) -> str:
        return f"{self._name} (ID: {self._agent_id}, 状态: {self._state.value})"
