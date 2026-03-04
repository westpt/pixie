"""
数据访问层（DAL）基类
封装数据库操作，提供统一的CRUD接口
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

# 数据库配置
DB_DIR = Path(__file__).parent / "data"
DB_FILE = DB_DIR / "agent.db"

# 配置日志
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """数据库错误基类"""
    pass

class NotFoundError(DatabaseError):
    """记录不存在错误"""
    pass

class DuplicateError(DatabaseError):
    """重复记录错误"""
    pass

class BaseDAL:
    """数据访问层基类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化DAL
        :param db_path: 数据库文件路径，默认使用agent.db
        """
        self.db_path = db_path or str(DB_FILE)
        self._ensure_db_dir()
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        DB_DIR.mkdir(parents=True, exist_ok=True)
        db_dir = Path(self.db_path).parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """
        获取数据库连接（上下文管理器）
        自动处理连接的打开与关闭
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 返回字典式行
            conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库连接错误：{str(e)}")
            raise DatabaseError(f"数据库连接失败：{str(e)}")
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Tuple = (), fetch_all: bool = False) -> List[Dict]:
        """
        执行查询语句
        :param query: SQL查询语句
        :param params: 查询参数
        :param fetch_all: 是否返回所有结果，False返回单条记录
        :return: 查询结果列表或单条记录
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                if fetch_all:
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    row = cursor.fetchone()
                    return dict(row) if row else None
            except sqlite3.Error as e:
                logger.error(f"查询执行错误：{str(e)}, SQL: {query}, 参数: {params}")
                raise DatabaseError(f"查询执行失败：{str(e)}")
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        执行更新/插入/删除语句
        :param query: SQL语句
        :param params: 语句参数
        :return: 影响的行数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                affected_rows = cursor.rowcount
                logger.debug(f"执行更新：{query}, 参数: {params}, 影响行数: {affected_rows}")
                return affected_rows
            except sqlite3.IntegrityError as e:
                conn.rollback()
                logger.error(f"数据完整性错误：{str(e)}, SQL: {query}, 参数: {params}")
                raise DuplicateError(f"数据完整性错误：{str(e)}")
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"更新执行错误：{str(e)}, SQL: {query}, 参数: {params}")
                raise DatabaseError(f"更新执行失败：{str(e)}")
    
    def execute_batch(self, query: str, params_list: List[Tuple]) -> int:
        """
        批量执行语句
        :param query: SQL语句
        :param params_list: 参数列表
        :return: 总影响行数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                affected_rows = cursor.rowcount
                logger.debug(f"批量执行：{query}, 参数数量: {len(params_list)}, 影响行数: {affected_rows}")
                return affected_rows
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"批量执行错误：{str(e)}, SQL: {query}")
                raise DatabaseError(f"批量执行失败：{str(e)}")
    
    def execute_transaction(self, queries: List[Tuple[str, Tuple]]) -> int:
        """
        执行事务（多个语句原子执行）
        :param queries: 语句列表，每个元素为(query, params)
        :return: 总影响行数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            total_affected = 0
            try:
                for query, params in queries:
                    cursor.execute(query, params)
                    total_affected += cursor.rowcount
                conn.commit()
                logger.debug(f"事务执行：{len(queries)}个语句, 总影响行数: {total_affected}")
                return total_affected
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"事务执行错误：{str(e)}")
                raise DatabaseError(f"事务执行失败：{str(e)}")
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        获取表信息
        :param table_name: 表名
        :return: 表信息字典
        """
        query = "PRAGMA table_info(?)"
        return self.execute_query(query, (table_name,), fetch_all=True)
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        :param table_name: 表名
        :return: 表是否存在
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_query(query, (table_name,))
        return result is not None
    
    def get_row_count(self, table_name: str, where_clause: str = None, params: Tuple = ()) -> int:
        """
        获取表的行数
        :param table_name: 表名
        :param where_clause: WHERE条件（可选）
        :param params: WHERE参数（可选）
        :return: 行数
        """
        if where_clause:
            query = f"SELECT COUNT(*) as count FROM {table_name} WHERE {where_clause}"
        else:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query, params)
        return result['count'] if result else 0
    
    def delete_all(self, table_name: str) -> int:
        """
        清空表数据
        :param table_name: 表名
        :return: 影响的行数
        """
        query = f"DELETE FROM {table_name}"
        return self.execute_update(query)
    
    def backup_table(self, table_name: str, backup_path: str) -> bool:
        """
        备份表数据
        :param table_name: 表名
        :param backup_path: 备份文件路径
        :return: 是否成功
        """
        try:
            import shutil
            import tempfile
            
            # 创建临时数据库
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as temp_file:
                temp_path = Path(temp_file.name)
                
                # 复制数据库
                shutil.copy2(self.db_path, temp_path)
                
                # 导出表数据
                with sqlite3.connect(temp_path) as temp_conn:
                    cursor = temp_conn.cursor()
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                # 写入备份文件
                backup_file = Path(backup_path)
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    # 写入CSV头
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row['name'] for row in cursor.fetchall()]
                    f.write(','.join(columns) + '\n')
                    
                    # 写入数据
                    for row in rows:
                        f.write(','.join(str(v) if v is not None else '' for v in row) + '\n')
                
                # 清理临时文件
                temp_path.unlink()
                
            logger.info(f"表 {table_name} 备份成功：{backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"表 {table_name} 备份失败：{str(e)}")
            return False

