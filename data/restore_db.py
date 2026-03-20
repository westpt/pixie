"""
数据库恢复脚本
支持从备份文件恢复数据库
"""

import sqlite3
import shutil
import sys
import gzip
import csv
import json
from pathlib import Path
from datetime import datetime
import argparse


# 数据库配置
DB_DIR = Path(__file__).parent / "data"
DB_FILE = DB_DIR / "agent.db"
BACKUP_DIR = Path(__file__).parent / "backup"


def restore_from_full_db(backup_path, verify_only=False):
    """
    从完整数据库备份恢复
    :param backup_path: 备份文件路径
    :param verify_only: 仅验证，不实际恢复
    :return: 是否成功
    """
    backup_path = Path(backup_path)

    if not backup_path.exists():
        print(f"错误：备份文件不存在 {backup_path}")
        return False

    # 检查备份文件类型
    is_compressed = backup_path.suffix == '.gz'

    if not verify_only:
        # 备份当前数据库
        if DB_FILE.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = DB_DIR / f"agent_before_restore_{timestamp}.db"
            print(f"正在备份当前数据库到：{current_backup}")
            shutil.copy2(DB_FILE, current_backup)

    try:
        if is_compressed:
            print(f"正在解压并恢复数据库：{backup_path}")
            if verify_only:
                # 仅验证压缩文件
                try:
                    with gzip.open(backup_path, 'rb') as f:
                        # 读取部分数据验证
                        f.read(1024)
                    print("备份文件验证成功！")
                    return True
                except Exception as e:
                    print(f"备份文件验证失败：{str(e)}")
                    return False

            # 解压并恢复
            with gzip.open(backup_path, 'rb') as f_in:
                with open(DB_FILE, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            print(f"正在恢复数据库：{backup_path}")
            if verify_only:
                # 仅验证文件
                try:
                    # 尝试打开数据库文件
                    test_conn = sqlite3.connect(backup_path)
                    test_conn.execute("SELECT 1")
                    test_conn.close()
                    print("备份文件验证成功！")
                    return True
                except Exception as e:
                    print(f"备份文件验证失败：{str(e)}")
                    return False

            # 直接复制
            shutil.copy2(backup_path, DB_FILE)

        if not verify_only:
            # 验证恢复的数据库
            print("验证恢复的数据库...")
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = cursor.fetchall()

            conn.close()

            print(f"恢复成功！")
            print(f"数据库位置：{DB_FILE}")
            print(f"恢复的表：{len(tables)} 个")

        return True

    except Exception as e:
        print(f"错误：恢复失败 - {str(e)}")
        return False


def restore_table_from_csv(csv_path, table_name=None, truncate=False):
    """
    从CSV文件恢复单个表
    :param csv_path: CSV文件路径
    :param table_name: 表名（可选，默认从文件名推断）
    :param truncate: 是否清空表后再恢复
    :return: 是否成功
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        print(f"错误：CSV文件不存在 {csv_path}")
        return False

    # 从文件名推断表名
    if table_name is None:
        table_name = csv_path.stem.split('_')[0]

    if not DB_FILE.exists():
        print(f"错误：数据库文件不存在 {DB_FILE}")
        return False

    try:
        print(f"正在从CSV恢复表 '{table_name}'：{csv_path}")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"错误：表 '{table_name}' 不存在")
            conn.close()
            return False

        # 读取CSV文件
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            columns = next(reader)  # 表头
            rows = list(reader)

        if truncate:
            # 清空表
            print(f"清空表 '{table_name}'...")
            cursor.execute(f"DELETE FROM {table_name}")

        # 插入数据
        placeholders = ','.join(['?'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"

        for row in rows:
            # 处理空字符串为None
            processed_row = [(None if v == '' else v) for v in row]
            cursor.execute(insert_query, processed_row)

        conn.commit()
        conn.close()

        print(f"恢复成功！")
        print(f"表名：{table_name}")
        print(f"插入记录：{len(rows)} 条")

        return True

    except Exception as e:
        print(f"错误：从CSV恢复失败 - {str(e)}")
        return False


def restore_from_json(json_path, verify_only=False, truncate=False):
    """
    从JSON备份恢复所有表
    :param json_path: JSON备份文件路径
    :param verify_only: 仅验证，不实际恢复
    :param truncate: 是否清空表后再恢复
    :return: 是否成功
    """
    json_path = Path(json_path)

    if not json_path.exists():
        print(f"错误：JSON备份文件不存在 {json_path}")
        return False

    try:
        print(f"正在读取JSON备份：{json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)

        if "tables" not in backup_data:
            print("错误：JSON备份格式不正确，缺少'tables'字段")
            return False

        print(f"备份时间：{backup_data.get('backup_time', '未知')}")
        print(f"包含表数：{len(backup_data['tables'])} 个")

        if verify_only:
            print("\n仅验证模式，不实际恢复")
            print("验证成功！")
            return True

        if not DB_FILE.exists():
            print(f"错误：数据库文件不存在 {DB_FILE}")
            return False

        # 备份当前数据库
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = DB_DIR / f"agent_before_restore_{timestamp}.db"
        print(f"正在备份当前数据库到：{current_backup}")
        shutil.copy2(DB_FILE, current_backup)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        total_inserted = 0

        for table_name, table_data in backup_data["tables"].items():
            print(f"\n恢复表：{table_name}")

            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"警告：表 '{table_name}' 不存在，跳过")
                continue

            if truncate:
                # 清空表
                cursor.execute(f"DELETE FROM {table_name}")

            if not table_data:
                print(f"  表为空，跳过")
                continue

            # 获取列名
            columns = list(table_data[0].keys())
            placeholders = ','.join(['?'] * len(columns))
            insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"

            # 插入数据
            inserted_count = 0
            for row_data in table_data:
                # 处理特殊类型
                processed_values = []
                for column in columns:
                    value = row_data.get(column)
                    if isinstance(value, (dict, list)):
                        processed_values.append(json.dumps(value, ensure_ascii=False))
                    else:
                        processed_values.append(value)
                try:
                    cursor.execute(insert_query, tuple(processed_values))
                    inserted_count += 1
                except Exception as e:
                    print(f"  警告：插入记录失败 - {str(e)}")
                    continue

            print(f"  插入记录：{inserted_count} 条")
            total_inserted += inserted_count

        conn.commit()
        conn.close()

        print(f"\n恢复成功！")
        print(f"总插入记录：{total_inserted} 条")

        return True

    except Exception as e:
        print(f"错误：从JSON恢复失败 - {str(e)}")
        return False


def list_backups():
    """列出所有备份文件"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

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
        file_type = "压缩备份" if backup_file.suffix == '.gz' else \
                   "JSON备份" if backup_file.suffix == '.json' else \
                   "CSV备份" if backup_file.suffix == '.csv' else "完整备份"
        print(f"{i}. {backup_file.name}")
        print(f"   类型: {file_type} | 大小: {size:.2f} KB | 修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def verify_backup(backup_path):
    """
    验证备份文件的完整性
    :param backup_path: 备份文件路径
    :return: 是否有效
    """
    backup_path = Path(backup_path)

    if not backup_path.exists():
        print(f"错误：备份文件不存在 {backup_path}")
        return False

    file_type = backup_path.suffix.lower()

    try:
        if file_type == '.gz':
            print("验证压缩备份文件...")
            return restore_from_full_db(backup_path, verify_only=True)
        elif file_type == '.json':
            print("验证JSON备份文件...")
            return restore_from_json(backup_path, verify_only=True)
        elif file_type == '.db':
            print("验证数据库备份文件...")
            return restore_from_full_db(backup_path, verify_only=True)
        else:
            print(f"警告：未知的备份文件类型 {file_type}")
            return False

    except Exception as e:
        print(f"验证失败：{str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Agent框架数据库恢复工具')

    parser.add_argument('backup_path', type=str, nargs='?', help='备份文件路径')
    parser.add_argument('--list', action='store_true', help='列出所有备份文件')
    parser.add_argument('--verify', action='store_true', help='仅验证备份文件，不恢复')
    parser.add_argument('--truncate', action='store_true', help='恢复前清空表')
    parser.add_argument('--table', type=str, help='指定表名（用于CSV恢复）')

    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.verify:
        if not args.backup_path:
            print("错误：验证备份需要指定备份文件路径")
            sys.exit(1)
        verify_backup(args.backup_path)
    elif args.backup_path:
        backup_path = Path(args.backup_path)

        # 根据文件类型选择恢复方式
        if backup_path.suffix == '.json':
            restore_from_json(args.backup_path, truncate=args.truncate)
        elif backup_path.suffix == '.csv':
            restore_table_from_csv(args.backup_path, table_name=args.table, truncate=args.truncate)
        else:
            restore_from_full_db(args.backup_path)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
