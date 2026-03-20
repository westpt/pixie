"""
数据库备份脚本
支持完整数据库备份和选择性表备份
"""

import sqlite3
import shutil
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse
import gzip
import json


# 数据库配置
DB_DIR = Path(__file__).parent / "data"
DB_FILE = DB_DIR / "agent.db"
BACKUP_DIR = Path(__file__).parent / "backup"


def ensure_backup_dir():
    """确保备份目录存在"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def backup_full_db(compress=True):
    """
    完整数据库备份
    :param compress: 是否压缩备份文件
    :return: 备份文件路径
    """
    ensure_backup_dir()

    if not DB_FILE.exists():
        print(f"错误：数据库文件不存在 {DB_FILE}")
        return None

    # 生成备份文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if compress:
        backup_filename = f"agent_backup_{timestamp}.db.gz"
        backup_path = BACKUP_DIR / backup_filename
    else:
        backup_filename = f"agent_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename

    try:
        if compress:
            # 压缩备份
            print(f"正在压缩备份数据库到：{backup_path}")
            with open(DB_FILE, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # 直接复制
            print(f"正在备份数据库到：{backup_path}")
            shutil.copy2(DB_FILE, backup_path)

        # 获取文件大小
        backup_size = backup_path.stat().st_size / 1024  # KB
        print(f"备份成功！")
        print(f"备份文件：{backup_path}")
        print(f"备份大小：{backup_size:.2f} KB")

        return backup_path

    except Exception as e:
        print(f"错误：备份失败 - {str(e)}")
        return None


def backup_table_to_csv(table_name, backup_path=None):
    """
    备份单个表到CSV格式
    :param table_name: 表名
    :param backup_path: 备份文件路径（可选）
    :return: 备份文件路径
    """
    ensure_backup_dir()

    if not DB_FILE.exists():
        print(f"错误：数据库文件不存在 {DB_FILE}")
        return None

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_path is None:
        backup_path = BACKUP_DIR / f"{table_name}_{timestamp}.csv"

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"错误：表 '{table_name}' 不存在")
            conn.close()
            return None

        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]

        # 导出数据
        print(f"正在备份表 '{table_name}' 到：{backup_path}")
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # 写入CSV文件
        import csv
        with open(backup_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)  # 写入表头
            for row in rows:
                # 处理None值和特殊字符
                processed_row = []
                for value in row:
                    if value is None:
                        processed_row.append('')
                    elif isinstance(value, (dict, list)):
                        processed_row.append(json.dumps(value, ensure_ascii=False))
                    else:
                        processed_row.append(str(value))
                writer.writerow(processed_row)

        conn.close()

        print(f"备份成功！")
        print(f"备份文件：{backup_path}")
        print(f"备份数据：{len(rows)} 条记录")

        return backup_path

    except Exception as e:
        print(f"错误：备份表失败 - {str(e)}")
        return None


def backup_all_tables_to_json():
    """
    将所有表备份为JSON格式
    :return: 备份文件路径
    """
    ensure_backup_dir()

    if not DB_FILE.exists():
        print(f"错误：数据库文件不存在 {DB_FILE}")
        return None

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"full_backup_{timestamp}.json"

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()

        backup_data = {
            "backup_time": datetime.now().isoformat(),
            "tables": {}
        }

        for table_row in tables:
            table_name = table_row[0]
            print(f"正在备份表：{table_name}")

            # 获取表数据
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # 转换为字典列表
            table_data = []
            for row in rows:
                row_dict = dict(row)
                # 处理特殊类型
                for key, value in row_dict.items():
                    if isinstance(value, str):
                        try:
                            # 尝试解析JSON
                            parsed = json.loads(value)
                            row_dict[key] = parsed
                        except:
                            pass
                table_data.append(row_dict)

            backup_data["tables"][table_name] = table_data

        # 写入JSON文件
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        conn.close()

        # 获取文件大小
        backup_size = backup_path.stat().st_size / 1024  # KB
        print(f"\n备份成功！")
        print(f"备份文件：{backup_path}")
        print(f"备份大小：{backup_size:.2f} KB")
        print(f"备份表数：{len(tables)}")

        return backup_path

    except Exception as e:
        print(f"错误：JSON备份失败 - {str(e)}")
        return None


def list_backups():
    """列出所有备份文件"""
    ensure_backup_dir()

    backup_files = list(BACKUP_DIR.glob("*"))

    if not backup_files:
        print("没有找到备份文件")
        return

    print(f"\n找到 {len(backup_files)} 个备份文件：\n")

    # 按修改时间排序
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    for i, backup_file in enumerate(backup_files, 1):
        size = backup_file.stat().st_size / 1024  # KB
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"{i}. {backup_file.name}")
        print(f"   大小: {size:.2f} KB | 修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def cleanup_old_backups(keep_days=7):
    """
    清理旧备份文件
    :param keep_days: 保留天数
    :return: 删除的文件数
    """
    ensure_backup_dir()

    backup_files = list(BACKUP_DIR.glob("*"))
    deleted_count = 0

    if not backup_files:
        print("没有找到备份文件")
        return 0

    cutoff_time = datetime.now().timestamp() - (keep_days * 86400)

    for backup_file in backup_files:
        if backup_file.stat().st_mtime < cutoff_time:
            try:
                backup_file.unlink()
                print(f"删除旧备份：{backup_file.name}")
                deleted_count += 1
            except Exception as e:
                print(f"删除失败：{backup_file.name} - {str(e)}")

    if deleted_count == 0:
        print(f"没有超过 {keep_days} 天的旧备份")
    else:
        print(f"\n共删除 {deleted_count} 个旧备份文件")

    return deleted_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Agent框架数据库备份工具')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--full', action='store_true', help='完整数据库备份')
    group.add_argument('--table', type=str, help='备份指定表（CSV格式）')
    group.add_argument('--json', action='store_true', help='JSON格式备份所有表')
    group.add_argument('--list', action='store_true', help='列出所有备份文件')
    group.add_argument('--cleanup', type=int, nargs='?', const=7, metavar='DAYS', help='清理旧备份（默认保留7天）')

    parser.add_argument('--no-compress', action='store_true', help='完整备份时不压缩')
    parser.add_argument('--output', type=str, help='指定备份输出路径')

    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.cleanup:
        cleanup_old_backups(keep_days=args.cleanup)
    elif args.full:
        backup_full_db(compress=not args.no_compress)
    elif args.json:
        backup_all_tables_to_json()
    elif args.table:
        backup_table_to_csv(args.table, backup_path=args.output)


if __name__ == '__main__':
    main()
