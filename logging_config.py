"""
日志配置模块
提供统一的日志配置和管理
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record):
        # 基础字段
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        # 添加可选字段
        if hasattr(record, 'agent_id'):
            log_data['agent_id'] = record.agent_id
        if hasattr(record, 'task_id'):
            log_data['task_id'] = record.task_id
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # JSON 格式
        return json.dumps(log_data, ensure_ascii=False)


class AgentLogger(logging.LoggerAdapter):
    """Agent 日志适配器，添加 Agent 相关上下文"""

    def __init__(self, logger: logging.Logger, agent_id: Optional[str] = None):
        super().__init__(logger, {})
        self.agent_id = agent_id

    def process(self, msg, kwargs):
        if self.agent_id:
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['agent_id'] = self.agent_id
        return msg, kwargs


class TaskLogger(logging.LoggerAdapter):
    """任务日志适配器，添加任务相关上下文"""

    def __init__(self, logger: logging.Logger, task_id: Optional[str] = None,
                 agent_id: Optional[str] = None):
        super().__init__(logger, {})
        self.task_id = task_id
        self.agent_id = agent_id

    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        if self.task_id:
            extra['task_id'] = self.task_id
        if self.agent_id:
            extra['agent_id'] = self.agent_id
        kwargs['extra'] = extra
        return msg, kwargs


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    log_dir: Optional[Path] = None,
    structured: bool = False
) -> logging.Logger:
    """
    设置日志系统

    :param level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    :param log_file: 日志文件路径
    :param log_dir: 日志目录（默认 logs/）
    :param structured: 是否使用结构化日志（JSON格式）
    :return: 根日志记录器
    """
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 确定日志目录
    if not log_dir:
        log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    # 创建格式化器
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        file_path = log_dir / log_file
    else:
        file_path = log_dir / f"agent_{datetime.now().strftime('%Y%m%d')}.log"

    file_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger


def get_agent_logger(logger: logging.Logger, agent_id: str) -> AgentLogger:
    """
    获取 Agent 日志记录器

    :param logger: 基础日志记录器
    :param agent_id: Agent ID
    :return: Agent 日志适配器
    """
    return AgentLogger(logger, agent_id)


def get_task_logger(logger: logging.Logger, task_id: str, agent_id: Optional[str] = None) -> TaskLogger:
    """
    获取任务日志记录器

    :param logger: 基础日志记录器
    :param task_id: 任务 ID
    :param agent_id: Agent ID（可选）
    :return: 任务日志适配器
    """
    return TaskLogger(logger, task_id, agent_id)


# 预定义的日志级别
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
