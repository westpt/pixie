"""
Agents表数据访问层
提供agents表的CRUD操作
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from data.dal import BaseDAL, DatabaseError, NotFoundError

logger = logging.getLogger(__name__)

class AgentsDAL(BaseDAL):
    """Agents表数据访问类"""
    
    def create_agent(self, name: str, agent_type: str, config: Dict[str, Any], 
                   status: str = 'created') -> int:
        """
        创建Agent记录
        :param name: Agent名称
        :param agent_type: Agent类型
        :param config: Agent配置（字典）
        :param status: Agent状态
        :return: Agent ID
        """
        query = """
            INSERT INTO agents (name, type, config, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        config_json = json.dumps(config, ensure_ascii=False)
        now = datetime.now().isoformat()
        
        try:
            agent_id = self.execute_update(query, (name, agent_type, config_json, status, now, now))
            logger.info(f"创建Agent成功：ID={agent_id}, name={name}, type={agent_type}")
            return agent_id
        except Exception as e:
            logger.error(f"创建Agent失败：{str(e)}")
            raise DatabaseError(f"创建Agent失败：{str(e)}")
    
    def get_agent_by_id(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取Agent
        :param agent_id: Agent ID
        :return: Agent信息字典，不存在返回None
        """
        query = "SELECT * FROM agents WHERE id = ?"
        result = self.execute_query(query, (agent_id,))
        
        if not result:
            return None
            
        # 解析配置JSON
        agent = dict(result)
        if agent.get('config'):
            try:
                agent['config'] = json.loads(agent['config'])
            except json.JSONDecodeError:
                logger.warning(f"Agent {agent_id} 的配置JSON解析失败")
                agent['config'] = {}
        
        return agent
    
    def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取Agent
        :param name: Agent名称
        :return: Agent信息字典，不存在返回None
        """
        query = "SELECT * FROM agents WHERE name = ?"
        result = self.execute_query(query, (name,))
        
        if not result:
            return None
            
        # 解析配置JSON
        agent = dict(result)
        if agent.get('config'):
            try:
                agent['config'] = json.loads(agent['config'])
            except json.JSONDecodeError:
                logger.warning(f"Agent {name} 的配置JSON解析失败")
                agent['config'] = {}
        
        return agent
    
    def get_all_agents(self, status: str = None, agent_type: str = None, 
                     limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取所有Agent
        :param status: 状态筛选（可选）
        :param agent_type: 类型筛选（可选）
        :param limit: 返回数量限制（可选）
        :param offset: 偏移量（可选，用于分页）
        :return: Agent列表
        """
        query = "SELECT * FROM agents WHERE 1=1"
        params = []
        
        # 添加筛选条件
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if agent_type:
            query += " AND type = ?"
            params.append(agent_type)
        
        # 添加排序和分页
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        results = self.execute_query(query, tuple(params), fetch_all=True)
        
        # 解析配置JSON
        agents = []
        for result in results:
            agent = dict(result)
            if agent.get('config'):
                try:
                    agent['config'] = json.loads(agent['config'])
                except json.JSONDecodeError:
                    agent['config'] = {}
            agents.append(agent)
        
        return agents
    
    def update_agent_status(self, agent_id: int, status: str) -> bool:
        """
        更新Agent状态
        :param agent_id: Agent ID
        :param status: 新状态
        :return: 是否成功
        """
        query = """
            UPDATE agents 
            SET status = ?, updated_at = ?
            WHERE id = ?
        """
        now = datetime.now().isoformat()
        
        affected = self.execute_update(query, (status, now, agent_id))

        if affected == 0:
            logger.warning(f"更新Agent状态失败：未找到ID={agent_id}的Agent")
            return False
        
        logger.info(f"更新Agent状态成功：ID={agent_id}, status={status}")
        return True
    
    def update_agent_config(self, agent_id: int, config: Dict[str, Any]) -> bool:
        """
        更新Agent配置
        :param agent_id: Agent ID
        :param config: 新配置（字典）
        :return: 是否成功
        """
        query = """
            UPDATE agents 
            SET config = ?, updated_at = ?
            WHERE id = ?
        """
        config_json = json.dumps(config, ensure_ascii=False)
        now = datetime.now().isoformat()
        
        affected = self.execute_update(query, (config_json, now, agent_id))

        if affected == 0:
            logger.warning(f"更新Agent配置失败：未找到ID={agent_id}的Agent")
            return False
        
        logger.info(f"更新Agent配置成功：ID={agent_id}")
        return True
    
    def delete_agent(self, agent_id: int) -> bool:
        """
        删除Agent（级联删除相关任务和结果）
        :param agent_id: Agent ID
        :return: 是否成功
        """
        # 先检查Agent是否存在
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            logger.warning(f"删除Agent失败：未找到ID={agent_id}的Agent")
            return False
        
        # 删除Agent（数据库设置了外键级联删除）
        query = "DELETE FROM agents WHERE id = ?"
        affected = self.execute_update(query, (agent_id,))
        
        logger.info(f"删除Agent成功：ID={agent_id}, name={agent['name']}")
        return True
    
    def get_agents_count(self, status: str = None, agent_type: str = None) -> int:
        """
        获取Agent数量
        :param status: 状态筛选（可选）
        :param agent_type: 类型筛选（可选）
        :return: Agent数量
        """
        query = "SELECT COUNT(*) as count FROM agents WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if agent_type:
            query += " AND type = ?"
            params.append(agent_type)
        
        result = self.execute_query(query, tuple(params))
        return result['count'] if result else 0
    
    def get_running_agent(self) -> Optional[Dict[str, Any]]:
        """
        获取运行中的Agent（单Agent模式，最多一个）
        :return: 运行中的Agent信息，不存在返回None
        """
        query = "SELECT * FROM agents WHERE status = 'running' LIMIT 1"
        result = self.execute_query(query)
        
        if not result:
            return None
            
        # 解析配置JSON
        agent = dict(result)
        if agent.get('config'):
            try:
                agent['config'] = json.loads(agent['config'])
            except json.JSONDecodeError:
                agent['config'] = {}
        
        return agent
    
    def backup_agents(self, backup_path: str) -> bool:
        """
        备份agents表数据
        :param backup_path: 备份文件路径
        :return: 是否成功
        """
        return self.backup_table('agents', backup_path)

