"""
任务管理器实现
负责任务的创建、查询、执行、状态更新等操作
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.interfaces import ITaskManager
from data import TasksDAL, ResultsDAL

logger = logging.getLogger(__name__)


class TaskManager(ITaskManager):
    """任务管理器"""

    def __init__(self, tasks_dal: TasksDAL, results_dal: ResultsDAL, agent_manager):
        """
        初始化任务管理器
        :param tasks_dal: 任务数据访问层
        :param results_dal: 结果数据访问层
        :param agent_manager: Agent 管理器
        """
        self.tasks_dal = tasks_dal
        self.results_dal = results_dal
        self.agent_manager = agent_manager

    def create_task(self, content: str, task_type: str = 'sync', priority: str = 'medium') -> str:
        """
        创建任务
        :param content: 任务内容
        :param task_type: 任务类型
        :param priority: 优先级
        :return: 任务 ID
        """
        try:
            # 生成任务 ID
            task_id = str(uuid.uuid4())

            # 创建任务记录
            self.tasks_dal.create_task(
                task_id=task_id,
                content=content,
                task_type=task_type,
                priority=priority,
                status='pending'
            )

            logger.info(f"任务创建成功: {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"任务创建失败: {str(e)}")
            raise

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        :param task_id: 任务 ID
        :return: 任务信息
        """
        try:
            task_data = self.tasks_dal.get_task_by_id(task_id)
            if task_data:
                return {
                    'task_id': task_data['task_id'],
                    'content': task_data['content'],
                    'task_type': task_data['task_type'],
                    'priority': task_data['priority'],
                    'status': task_data['status'],
                    'created_at': task_data['created_at'].isoformat() if task_data['created_at'] else None,
                    'updated_at': task_data['updated_at'].isoformat() if task_data['updated_at'] else None,
                    'assigned_agent_id': task_data.get('assigned_agent_id'),
                    'completed_at': task_data['completed_at'].isoformat() if task_data.get('completed_at') else None
                }
            return None
        except Exception as e:
            logger.error(f"获取任务信息失败: {str(e)}")
            return None

    def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        列出所有任务
        :param filters: 过滤条件
        :return: 任务列表
        """
        try:
            tasks = self.tasks_dal.get_all_tasks()

            # 应用过滤
            if filters:
                if 'status' in filters:
                    tasks = [t for t in tasks if t['status'] == filters['status']]
                if 'task_type' in filters:
                    tasks = [t for t in tasks if t['task_type'] == filters['task_type']]
                if 'priority' in filters:
                    tasks = [t for t in tasks if t['priority'] == filters['priority']]
                if 'assigned_agent_id' in filters:
                    tasks = [t for t in tasks if t.get('assigned_agent_id') == filters['assigned_agent_id']]

            # 转换为字典列表
            return [
                {
                    'task_id': t['task_id'],
                    'content': t['content'],
                    'task_type': t['task_type'],
                    'priority': t['priority'],
                    'status': t['status'],
                    'created_at': t['created_at'].isoformat() if hasattr(t['created_at'], 'isoformat') else t['created_at'],
                    'assigned_agent_id': t.get('assigned_agent_id')
                }
                for t in tasks
            ]
        except Exception as e:
            logger.error(f"列出任务失败: {str(e)}")
            return []

    def update_task_status(self, task_id: str, status: str, assigned_agent_id: str = None) -> bool:
        """
        更新任务状态
        :param task_id: 任务 ID
        :param status: 新状态
        :param assigned_agent_id: 分配的 Agent ID（可选）
        :return: 是否成功
        """
        try:
            updates = {'status': status}
            if assigned_agent_id:
                updates['assigned_agent_id'] = assigned_agent_id

            if status == 'completed':
                updates['completed_at'] = datetime.now()

            self.tasks_dal.update_task(task_id, updates)
            logger.info(f"任务状态更新成功: {task_id} -> {status}")
            return True

        except Exception as e:
            logger.error(f"任务状态更新失败: {str(e)}")
            return False

    def execute_task(self, task_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行任务
        :param task_id: 任务 ID
        :param agent_id: Agent ID（可选）
        :return: 执行结果
        """
        try:
            # 获取任务
            task = self.tasks_dal.get_task_by_id(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")

            # 获取或加载 Agent
            if not agent_id:
                # 如果没有指定 Agent，使用默认 Agent
                agents = self.agent_manager.list_agents()
                if not agents:
                    raise ValueError("没有可用的 Agent")
                agent_id = agents[0]['agent_id']

            # 加载 Agent
            agent = self.agent_manager.get_loaded_agent(agent_id)
            if not agent:
                if not self.agent_manager.load_agent(agent_id):
                    raise ValueError(f"Agent 加载失败: {agent_id}")
                agent = self.agent_manager.get_loaded_agent(agent_id)

            # 更新任务状态为处理中
            self.update_task_status(task_id, 'processing', agent_id)

            # 执行任务
            task_data = {
                'task_id': task_id,
                'content': task['content'],
                'task_type': task['task_type']
            }

            result_data = agent.process_task(task_data)

            # 保存结果
            self.results_dal.create_result(
                task_id=task_id,
                content=result_data.get('content', ''),
                format=result_data.get('format', 'text'),
                execution_time=result_data.get('execution_time'),
                status=result_data.get('status', 'success')
            )

            # 更新任务状态
            final_status = 'completed' if result_data.get('status') == 'success' else 'failed'
            self.update_task_status(task_id, final_status)

            logger.info(f"任务执行完成: {task_id}, 状态: {final_status}")

            return {
                'task_id': task_id,
                'status': final_status,
                'result': result_data
            }

        except Exception as e:
            logger.error(f"任务执行失败: {str(e)}")
            self.update_task_status(task_id, 'failed')
            return {
                'task_id': task_id,
                'status': 'failed',
                'result': {'content': str(e), 'status': 'failed'}
            }

    def decompose_task(self, content: str) -> List[Dict[str, Any]]:
        """
        任务拆解（简化版）
        :param content: 任务内容
        :return: 子任务列表
        """
        # TODO: 实现智能任务拆解（使用大模型）
        # 当前返回单个任务
        return [
            {
                'content': content,
                'task_type': 'sync',
                'priority': 'medium'
            }
        ]

    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务结果
        :param task_id: 任务 ID
        :return: 任务结果
        """
        try:
            result = self.results_dal.get_result_by_task_id(task_id)
            if result:
                return {
                    'task_id': result['task_id'],
                    'content': result['content'],
                    'format': result['format'],
                    'execution_time': result['execution_time'],
                    'status': result['status'],
                    'created_at': result['created_at'].isoformat() if result['created_at'] else None
                }
            return None
        except Exception as e:
            logger.error(f"获取任务结果失败: {str(e)}")
            return None
