"""
Agent 管理器实现
负责 Agent 的注册、查询、更新、删除等操作
"""

import logging
from typing import Dict, Any, List, Optional
from core.interfaces import IAgentManager
from agent_core import QAAssistant
from data import AgentsDAL

logger = logging.getLogger(__name__)


class AgentManager(IAgentManager):
    """Agent 管理器"""

    def __init__(self, agents_dal: AgentsDAL):
        """
        初始化 Agent 管理器
        :param agents_dal: Agent 数据访问层
        """
        self.agents_dal = agents_dal
        self._loaded_agents = {}  # 运行时缓存的 Agent 实例

    def register_agent(self, config: Dict[str, Any]) -> str:
        """
        注册新 Agent
        :param config: Agent 配置
        :return: Agent ID
        """
        try:
            # 验证配置
            name = config.get('name')
            if not name:
                raise ValueError("Agent 名称不能为空")

            # 创建 Agent 实例
            agent = QAAssistant(config)
            agent_id = agent.agent_id

            # 保存到数据库（注意：这里使用整数 ID）
            db_id = self.agents_dal.create_agent(
                name=agent.name,
                agent_type=agent.agent_type,
                config=config,
                status='created'
            )

            # 使用数据库返回的 ID 作为运行时键
            runtime_id = str(db_id)
            self._loaded_agents[runtime_id] = agent

            logger.info(f"Agent 注册成功: {name} (DB ID: {db_id})")
            return runtime_id

        except Exception as e:
            logger.error(f"Agent 注册失败: {str(e)}")
            raise

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 信息
        :param agent_id: Agent ID (字符串形式的数据库 ID)
        :return: Agent 信息
        """
        try:
            # 将字符串 ID 转换为整数
            try:
                db_id = int(agent_id)
            except ValueError:
                logger.error(f"无效的 Agent ID: {agent_id}")
                return None

            agent_data = self.agents_dal.get_agent_by_id(db_id)
            if agent_data:
                # 统一字段名：id -> agent_id, type -> agent_type
                return {
                    'agent_id': str(agent_data['id']),  # 统一使用字符串
                    'name': agent_data['name'],
                    'type': agent_data['type'],  # 数据库中是 'type'
                    'status': agent_data['status'],
                    'created_at': agent_data['created_at'].isoformat() if agent_data['created_at'] else None,
                    'config': agent_data.get('config', {})
                }
            return None
        except Exception as e:
            logger.error(f"获取 Agent 信息失败: {str(e)}")
            return None

    def list_agents(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        列出所有 Agent
        :param filters: 过滤条件
        :return: Agent 列表
        """
        try:
            agents = self.agents_dal.get_all_agents()

            # 应用过滤
            if filters:
                if 'status' in filters:
                    agents = [a for a in agents if a['status'] == filters['status']]
                if 'type' in filters:
                    agents = [a for a in agents if a['type'] == filters['type']]

            # 转换为字典列表
            return [
                {
                    'agent_id': str(a['id']),  # 统一使用字符串
                    'name': a['name'],
                    'type': a['type'],
                    'status': a['status'],
                    'created_at': a['created_at'].isoformat() if hasattr(a['created_at'], 'isoformat') else a['created_at']
                }
                for a in agents
            ]
        except Exception as e:
            logger.error(f"列出 Agent 失败: {str(e)}")
            return []

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新 Agent 信息
        :param agent_id: Agent ID
        :param updates: 更新内容
        :return: 是否成功
        """
        try:
            # 检查 Agent 是否存在
            if not self.get_agent(agent_id):
                logger.error(f"Agent 不存在: {agent_id}")
                return False

            # 转换为数据库 ID
            try:
                db_id = int(agent_id)
            except ValueError:
                logger.error(f"无效的 Agent ID: {agent_id}")
                return False

            # 更新数据库（使用 DAL 提供的更新方法）
            if 'config' in updates:
                self.agents_dal.update_agent_config(db_id, updates['config'])
            if 'status' in updates:
                self.agents_dal.update_agent_status(db_id, updates['status'])

            # 如果 Agent 已加载，更新配置
            if agent_id in self._loaded_agents:
                agent = self._loaded_agents[agent_id]
                if 'config' in updates:
                    agent.config.update(updates['config'])

            logger.info(f"Agent 更新成功: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Agent 更新失败: {str(e)}")
            return False

    def delete_agent(self, agent_id: str) -> bool:
        """
        删除 Agent
        :param agent_id: Agent ID
        :return: 是否成功
        """
        try:
            # 检查是否有关联任务
            from data import TasksDAL
            tasks_dal = TasksDAL()

            # 转换为数据库 ID
            try:
                db_id = int(agent_id)
            except ValueError:
                logger.error(f"无效的 Agent ID: {agent_id}")
                return False

            # 使用现有的方法检查处理中的任务
            tasks = tasks_dal.get_processing_tasks(db_id)
            if tasks:
                logger.error(f"Agent 有关联任务，无法删除: {agent_id}")
                return False

            # 从数据库删除
            self.agents_dal.delete_agent(db_id)

            # 从缓存移除
            if agent_id in self._loaded_agents:
                del self._loaded_agents[agent_id]

            logger.info(f"Agent 删除成功: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Agent 删除失败: {str(e)}")
            return False

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 状态
        :param agent_id: Agent ID
        :return: 状态信息
        """
        try:
            # 获取数据库中的状态
            try:
                db_id = int(agent_id)
            except ValueError:
                logger.error(f"无效的 Agent ID: {agent_id}")
                return None

            agent_data = self.agents_dal.get_agent_by_id(db_id)
            if not agent_data:
                return None

            # 如果 Agent 已加载到运行时，获取实时状态
            if agent_id in self._loaded_agents:
                agent = self._loaded_agents[agent_id]
                info = agent.get_info()
                return {
                    'status': info['status'],
                    'processed_count': info['processed_count'],
                    'error_count': info['error_count'],
                    'current_task': info['current_task'],
                    'updated_at': info['updated_at']
                }

            # 返回数据库状态
            return {
                'status': agent_data['status'],
                'processed_count': 0,
                'error_count': 0,
                'current_task': None,
                'updated_at': agent_data['updated_at'].isoformat() if agent_data['updated_at'] else None
            }

        except Exception as e:
            logger.error(f"获取 Agent 状态失败: {str(e)}")
            return None

    def load_agent(self, agent_id: str) -> bool:
        """
        加载 Agent 到运行时
        :param agent_id: Agent ID
        :return: 是否成功
        """
        try:
            # 如果已加载，直接返回
            if agent_id in self._loaded_agents:
                return True

            # 从数据库加载
            try:
                db_id = int(agent_id)
            except ValueError:
                logger.error(f"无效的 Agent ID: {agent_id}")
                return False

            agent_data = self.agents_dal.get_agent_by_id(db_id)
            if not agent_data:
                logger.error(f"Agent 不存在: {agent_id}")
                return False

            # 创建 Agent 实例
            config = agent_data.get('config', {})
            agent = QAAssistant(config)

            # 缓存到运行时
            self._loaded_agents[agent_id] = agent

            # 更新数据库状态
            self.agents_dal.update_agent_status(db_id, 'running')

            logger.info(f"Agent 加载成功: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Agent 加载失败: {str(e)}")
            return False

    def get_loaded_agent(self, agent_id: str):
        """
        获取已加载的 Agent 实例
        :param agent_id: Agent ID
        :return: Agent 实例或 None
        """
        return self._loaded_agents.get(agent_id)

    def unload_agent(self, agent_id: str) -> bool:
        """
        卸载 Agent
        :param agent_id: Agent ID
        :return: 是否成功
        """
        try:
            if agent_id in self._loaded_agents:
                agent = self._loaded_agents[agent_id]
                agent.stop()
                del self._loaded_agents[agent_id]

                # 转换为数据库 ID
                try:
                    db_id = int(agent_id)
                except ValueError:
                    return False

                # 更新数据库状态
                self.agents_dal.update_agent_status(db_id, 'stopped')

                logger.info(f"Agent 卸载成功: {agent_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Agent 卸载失败: {str(e)}")
            return False
