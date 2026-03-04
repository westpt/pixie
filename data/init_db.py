"""
数据库初始化脚本
初始化SQLite数据库，创建表结构
"""

import sqlite3
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.models import (
    AGENTS_TABLE_SCHEMA,
    TASKS_TABLE_SCHEMA,
    RESULTS_TABLE_SCHEMA,
    CONFIG_HISTORY_TABLE_SCHEMA
)

# 数据库配置
DB_DIR = Path(__file__).parent / "data"
DB_FILE = DB_DIR / "agent.db"

def ensure_db_dir():
    """确保数据库目录存在"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.parent.mkdir(parents=True, exist_ok=True)

def init_database(reset=False):
    """
    初始化数据库
    :param reset: 是否重置数据库（删除后重新创建）
    """
    ensure_db_dir()
    
    # 如果重置，删除旧数据库
    if reset and DB_FILE.exists():
        print(f"删除旧数据库：{DB_FILE}")
        os.remove(DB_FILE)
    
    # 连接数据库
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 创建表
        print("创建agents表...")
        cursor.executescript(AGENTS_TABLE_SCHEMA)
        
        print("创建tasks表...")
        cursor.executescript(TASKS_TABLE_SCHEMA)
        
        print("创建results表...")
        cursor.executescript(RESULTS_TABLE_SCHEMA)
        
        print("创建config_history表...")
        cursor.executescript(CONFIG_HISTORY_TABLE_SCHEMA)
        
        # 提交事务
        conn.commit()
        
        print(f"\n数据库初始化成功！")
        print(f"数据库位置：{DB_FILE}")
        print(f"数据库大小：{DB_FILE.stat().st_size / 1024:.2f} KB")
        
        # 显示表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        print(f"\n已创建的表：{len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        conn.rollback()
        print(f"错误：数据库初始化失败 - {str(e)}")
        raise
    finally:
        conn.close()

def verify_database():
    """验证数据库完整性"""
    if not DB_FILE.exists():
        print("错误：数据库文件不存在")
        return False
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        required_tables = ['agents', 'tasks', 'results', 'config_history']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = set(required_tables) - set(existing_tables)
        
        if missing_tables:
            print(f"错误：缺少表：{missing_tables}")
            return False
        
        print("数据库验证成功！")
        return True
        
    except Exception as e:
        print(f"错误：数据库验证失败 - {str(e)}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='初始化Agent框架数据库')
    parser.add_argument('--reset', action='store_true', help='重置数据库（删除后重新创建）')
    parser.add_argument('--verify', action='store_true', help='验证数据库完整性')
    
    args = parser.parse_args()
    
    if args.verify:
        # 验证模式
        success = verify_database()
        sys.exit(0 if success else 1)
    else:
        # 初始化模式
        init_database(reset=args.reset)

if __name__ == '__main__':
    main()

