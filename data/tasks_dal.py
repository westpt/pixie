"""
Tasks表数据访问层
提供tasks表的CRUD操作
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from data.dal import BaseDAL, DatabaseError

logger = logging.getLogger(__name__)

class TasksDAL(BaseDAL):
    """Tasks表数据访问类"""
    
    def create_task(self, task_id: str, content: str, task_type: str = 'sync',
                   priority: str = 'medium', status: str = 'pending',
                   agent_id: Optional[int] = None) -> int:
        """
        创建任务记录
        :param task_id: 任务ID
        :param content: 任务内容
        :param task_type: 任务类型（sync/async）
        :param priority: 优先级（low/medium/high）
        :param status: 任务状态
        :param agent_id: 分配的Agent ID（可选）
        :return: 任务内部ID
        """
        query = """
            INSERT INTO tasks (task_id, content, task_type, priority, status, agent_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        
        try:
            internal_id = self.execute_update(query, (task_id, content, task_type, priority, status, agent_id, now))
            logger.info(f"创建任务成功：task_id={task_id}, internal_id={internal_id}")
            return internal_id
        except Exception as e:
            logger.error(f"创建任务失败：{str(e)}")
            raise DatabaseError(f"创建任务失败：{str(e)}")
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        根据task_id获取任务
        :param task_id: 任务ID
        :return: 任务信息字典，不存在返回None
        """
        query = "SELECT * FROM tasks WHERE task_id = ?"
        result = self.execute_query(query, (task_id,))
        return dict(result) if result else None
    
    def get_task_by_internal_id(self, internal_id: int) -> Optional[Dict[str, Any]]:
        """
        根据内部ID获取任务
        :param internal_id: 内部ID
        :return: 任务信息字典，不存在返回None
        """
        query = "SELECT * FROM tasks WHERE id = ?"
        result = self.execute_query(query, (internal_id,))
        return dict(result) if result else None
    
    def get_all_tasks(self, status: str = None, task_type: str = None,
                     agent_id: Optional[int] = None, priority: str = None,
                     limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取所有任务
        :param status: 状态筛选（可选）
        :param task_type: 类型筛选（可选）
        :param agent_id: Agent筛选（可选）
        :param priority: 优先级筛选（可选）
        :param limit: 返回数量限制（可选）
        :param offset: 偏移量（可选，用于分页）
        :return: 任务列表
        """
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        # 添加筛选条件
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        
        if agent_id is not None:
            query += " AND agent_id = ?"
            params.append(agent_id)
        
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        
        # 添加排序和分页
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        results = self.execute_query(query, tuple(params), fetch_all=True)
        return [dict(row) for row in results]
    
    def update_task_status(self, task_id: str, status: str, 
                        agent_id: Optional[int] = None) -> bool:
        """
        更新任务状态
        :param task_id: 任务ID
        :param status: 新状态
        :param agent_id: 分配的Agent ID（可选）
        :return: 是否成功
        """
        # 根据状态更新不同字段
        if status == 'processing':
            query = """
                UPDATE tasks 
                    SET status = ?, agent_id = ?, started_at = ?
                    WHERE task_id = ?
            """
            now = datetime.now().isoformat()
            params = (status, agent_id, now, task_id)
        elif status in ['completed', 'failed']:
            query = """
                UPDATE tasks 
                    SET status = ?, completed_at = ?
                    WHERE task_id = ?
            """
            now = datetime.now().isoformat()
            params = (status, now, task_id)
        else:
            query = """
                UPDATE tasks 
                    SET status = ?
                    WHERE task_id = ?
            """
            params = (status, task_id)
        
        affected = self.execute_update(query, params)
        
        if affected > 0:
            logger.warning(f"更新任务状态失败：未找到task_id={task_id}的任务")
            return False
        
        logger.info(f"更新任务状态成功：task_id={task_id}, status={status}")
        return True
    
    def update_task_agent(self, task_id: str, agent_id: int) -> bool:
        """
        更新任务的分配Agent
        :param task_id: 任务ID
        :param agent_id: Agent ID
        :return: 是否成功
        """
        query = "UPDATE tasks SET agent_id = ? WHERE task_id = ?"
        affected = self.execute_update(query, (agent_id, task_id))
        
        if affected > 0:
            logger.warning(f"更新任务Agent失败：未找到task_id={task_id}的任务")
            return False
        
        logger.info(f"更新任务Agent成功：task_id={task_id}, agent_id={agent_id}")
        return True
    
    def get_tasks_count(self, status: str = None, task_type: str = None,
                       agent_id: Optional[int] = None) -> int:
        """
        获取任务数量
        :param status: 状态筛选（可选）
        :param task_type: 类型筛选（可选）
        :param agent_id: Agent筛选（可选）
        :return: 任务数量
        """
        query = "SELECT COUNT(*) as count FROM tasks WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        
        if agent_id is not None:
            query += " AND agent_id = ?"
            params.append(agent_id)
        
        result = self.execute_query(query, tuple(params))
        return result['count'] if result else 0
    
    def get_pending_tasks(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取待处理任务（按优先级排序）
        :param limit: 返回数量限制
        :return: 待处理任务列表
        """
        query = """
            SELECT * FROM tasks 
            WHERE status = 'pending'
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                created_at ASC
        """
        
        if limit:
            query += " LIMIT ?"
            return self.execute_query(query, (limit,), fetch_all=True)
        else:
            return self.execute_query(query, fetch_all=True)
    
    def get_processing_tasks(self, agent_id: int) -> List[Dict[str, Any]]:
        """
        获取Agent正在处理的任务
        :param agent_id: Agent ID
        :return: 处理中的任务列表
        """
        query = "SELECT * FROM tasks WHERE agent_id = ? AND status = 'processing'"
        return self.execute_query(query, (agent_id,), fetch_all=True)
    
    def get_tasks_by_date_range(self, start_date: str, end_date: str, 
                               status: str = None) -> List[Dict[str, Any]]:
        """
        按日期范围获取任务
        :param start_date: 开始日期（ISO格式）
        :param end_date: 结束日期（ISO格式）
        :param status: 状态筛选（可选）
        :return: 任务列表
        """
        query = "SELECT * FROM tasks WHERE created_at >= ? AND created_at <= ?"
        params = [start_date, end_date]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        results = self.execute_query(query, tuple(params), fetch_all=True)
        return [dict(row) for row in results]
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务（级联删除相关结果）
        :param task_id: 任务ID
        :return: 是否成功
        """
        query = "DELETE FROM tasks WHERE task_id = ?"
        affected = self.execute_update(query, (task_id,))
        
        logger.info(f"删除任务成功：task_id={task_id}")
        return affected > 0
    
    def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        清理旧任务数据
        :param days: 保留天数
        :return: 删除的任务数
        """
        query = """
            DELETE FROM tasks 
            WHERE created_at < datetime('now', '-' || ? || ' days')
                AND status IN ('completed', 'failed')
        """
        affected = self.execute_update(query, (days,))
        logger.info(f"清理旧任务：删除了{affected}个{days}天前的任务")
        return affected
    
    def backup_tasks(self, backup_path: str) -> bool:
        """
        备份tasks表数据
        :param backup_path: 备份文件路径
        :return: 是否成功
        """
        return self.backup_table('tasks', backup_path)

