"""
Results表数据访问层
提供results表的CRUD操作
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from data.dal import BaseDAL, DatabaseError

logger = logging.getLogger(__name__)

class ResultsDAL(BaseDAL):
    """Results表数据访问类"""
    
    def create_result(self, task_id: str, content: str, 
                    format: str = 'text', execution_time: float = None,
                    status: str = 'success') -> int:
        """
        创建结果记录
        :param task_id: 任务ID
        :param content: 结果内容
        :param format: 结果格式（text/json/html/markdown）
        :param execution_time: 执行时间（秒）
        :param status: 结果状态（success/failed）
        :return: 结果内部ID
        """
        query = """
            INSERT INTO results (task_id, content, format, execution_time, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        
        try:
            result_id = self.execute_update(query, (task_id, content, format, execution_time, status, now))
            logger.info(f"创建结果成功：ID={result_id}, task_id={task_id}")
            return result_id
        except Exception as e:
            logger.error(f"创建结果失败：{str(e)}")
            raise DatabaseError(f"创建结果失败：{str(e)}")
    
    def get_result_by_task_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        根据任务ID获取结果
        :param task_id: 任务ID
        :return: 结果信息字典，不存在返回None
        """
        query = "SELECT * FROM results WHERE task_id = ?"
        result = self.execute_query(query, (task_id,))
        return dict(result) if result else None
    
    def get_all_results(self, status: str = None, format: str = None,
                       task_id: Optional[str] = None,
                       limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取所有结果
        :param status: 状态筛选（可选）
        :param format: 格式筛选（可选）
        :param task_id: 任务ID筛选（可选）
        :param limit: 返回数量限制（可选）
        :param offset: 偏移量（可选，用于分页）
        :return: 结果列表
        """
        query = "SELECT * FROM results WHERE 1=1"
        params = []
        
        # 添加筛选条件
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if format:
            query += " AND format = ?"
            params.append(format)
        
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        
        # 添加排序和分页
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        results = self.execute_query(query, tuple(params), fetch_all=True)
        return [dict(row) for row in results]
    
    def get_results_by_date_range(self, start_date: str, end_date: str,
                                  status: str = None) -> List[Dict[str, Any]]:
        """
        按日期范围获取结果
        :param start_date: 开始日期（ISO格式）
        :param end_date: 结束日期（ISO格式）
        :param status: 状态筛选（可选）
        :return: 结果列表
        """
        query = "SELECT * FROM results WHERE created_at >= ? AND created_at <= ?"
        params = [start_date, end_date]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        results = self.execute_query(query, tuple(params), fetch_all=True)
        return [dict(row) for row in results]
    
    def get_result_by_internal_id(self, internal_id: int) -> Optional[Dict[str, Any]]:
        """
        根据内部ID获取结果
        :param internal_id: 内部ID
        :return: 结果信息字典，不存在返回None
        """
        query = "SELECT * FROM results WHERE id = ?"
        result = self.execute_query(query, (internal_id,))
        return dict(result) if result else None
    
    def get_results_count(self, status: str = None, format: str = None,
                          task_id: Optional[str] = None) -> int:
        """
        获取结果数量
        :param status: 状态筛选（可选）
        :param format: 格式筛选（可选）
        :param task_id: 任务ID筛选（可选）
        :return: 结果数量
        """
        query = "SELECT COUNT(*) as count FROM results WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if format:
            query += " AND format = ?"
            params.append(format)
        
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        
        result = self.execute_query(query, tuple(params))
        return result['count'] if result else 0
    
    def get_success_rate(self, start_date: str = None, end_date: str = None) -> float:
        """
        获取成功率
        :param start_date: 开始日期（可选）
        :param end_date: 结束日期（可选）
        :return: 成功率（0-1之间）
        """
        if start_date and end_date:
            query = """
                SELECT 
                    CAST(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) as success_rate
                    FROM results
                    WHERE created_at >= ? AND created_at <= ?
            """
            result = self.execute_query(query, (start_date, end_date))
        else:
            query = """
                SELECT 
                    CAST(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) as success_rate
                    FROM results
            """
            result = self.execute_query(query)
        
        if result:
            return result['success_rate'] or 0.0
        return 0.0
    
    def get_average_execution_time(self, status: str = 'success') -> Optional[float]:
        """
        获取平均执行时间
        :param status: 状态筛选（默认success）
        :return: 平均执行时间（秒），无数据返回None
        """
        query = """
            SELECT AVG(execution_time) as avg_time
                FROM results
                WHERE status = ? AND execution_time IS NOT NULL
        """
        result = self.execute_query(query, (status,))
        
        if result:
            return result['avg_time']
        return None
    
    def delete_result_by_task_id(self, task_id: str) -> bool:
        """
        根据任务ID删除结果
        :param task_id: 任务ID
        :return: 是否成功
        """
        query = "DELETE FROM results WHERE task_id = ?"
        affected = self.execute_update(query, (task_id,))
        
        logger.info(f"删除结果成功：task_id={task_id}")
        return affected > 0
    
    def cleanup_old_results(self, days: int = 30) -> int:
        """
        清理旧结果数据
        :param days: 保留天数
        :return: 删除的结果数
        """
        query = """
            DELETE FROM results 
            WHERE created_at < datetime('now', '-' || ? || ' days')
                AND status IN ('success', 'failed')
        """
        affected = self.execute_update(query, (days,))
        logger.info(f"清理旧结果：删除了{affected}个{days}天前的结果")
        return affected
    
    def backup_results(self, backup_path: str) -> bool:
        """
        备份results表数据
        :param backup_path: 备份文件路径
        :return: 是否成功
        """
        return self.backup_table('results', backup_path)

