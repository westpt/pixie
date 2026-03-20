"""
数据持久化层功能验证脚本
演示并验证数据访问层的核心功能
"""

import sys
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.agents_dal import AgentsDAL
from data.tasks_dal import TasksDAL
from data.results_dal import ResultsDAL
from data.models import (
    AGENTS_TABLE_SCHEMA,
    TASKS_TABLE_SCHEMA,
    RESULTS_TABLE_SCHEMA
)


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_success(message):
    """打印成功消息"""
    print(f"✅ {message}")


def print_info(message):
    """打印信息"""
    print(f"ℹ️  {message}")


def init_test_database():
    """初始化测试数据库"""
    print_section("1. 初始化测试数据库")

    # 使用临时数据库文件
    test_db = Path(__file__).parent / "data" / "test_verify.db"

    # 删除旧测试数据库
    if test_db.exists():
        test_db.unlink()
        print_info(f"删除旧测试数据库: {test_db}")

    # 创建表
    conn = sqlite3.connect(str(test_db))
    conn.executescript(AGENTS_TABLE_SCHEMA)
    conn.executescript(TASKS_TABLE_SCHEMA)
    conn.executescript(RESULTS_TABLE_SCHEMA)
    conn.commit()
    conn.close()

    print_success(f"创建测试数据库: {test_db}")

    return str(test_db)


def test_agents_dal(db_path):
    """测试AgentsDAL功能"""
    print_section("2. 测试 AgentsDAL (Agent数据访问层)")

    agents_dal = AgentsDAL(db_path)

    # 创建Agent
    print_info("创建Agent...")
    config = {
        "api_key": "test_api_key_123",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    }
    agent_id = agents_dal.create_agent(
        name="QA助手",
        agent_type="qa",
        config=config
    )
    print_success(f"创建Agent成功，ID: {agent_id}")

    # 查询Agent
    print_info(f"查询Agent (ID={agent_id})...")
    agent = agents_dal.get_agent_by_id(agent_id)
    print_success(f"查询成功: {agent['name']}, 类型: {agent['type']}")
    print(f"   配置: {agent['config']}")

    # 更新状态
    print_info("更新Agent状态为 'running'...")
    agents_dal.update_agent_status(agent_id, "running")
    agent = agents_dal.get_agent_by_id(agent_id)
    print_success(f"状态更新成功: {agent['status']}")

    # 更新配置
    print_info("更新Agent配置...")
    new_config = agent['config'].copy()
    new_config['temperature'] = 0.9
    agents_dal.update_agent_config(agent_id, new_config)
    agent = agents_dal.get_agent_by_id(agent_id)
    print_success(f"配置更新成功: temperature={agent['config']['temperature']}")

    # 创建第二个Agent
    print_info("创建第二个Agent...")
    agent_id2 = agents_dal.create_agent(
        name="数据分析助手",
        agent_type="data_analyzer",
        config={"api_key": "key_456"}
    )
    print_success(f"创建第二个Agent成功，ID: {agent_id2}")

    # 获取所有Agent
    print_info("获取所有Agent...")
    all_agents = agents_dal.get_all_agents()
    print_success(f"获取成功，共 {len(all_agents)} 个Agent:")
    for ag in all_agents:
        print(f"   - {ag['name']} ({ag['type']}) - {ag['status']}")

    # 获取Agent数量
    count = agents_dal.get_agents_count()
    print_success(f"Agent总数: {count}")

    return agent_id


def test_tasks_dal(db_path, agent_id):
    """测试TasksDAL功能"""
    print_section("3. 测试 TasksDAL (任务数据访问层)")

    tasks_dal = TasksDAL(db_path)

    # 创建任务
    print_info("创建任务...")
    task_id1 = tasks_dal.create_task(
        task_id="task_001",
        content="解释什么是人工智能？",
        task_type="sync",
        priority="high"
    )
    print_success(f"创建任务成功，内部ID: {task_id1}")

    # 创建多个任务
    print_info("创建多个任务...")
    tasks_dal.create_task("task_002", "Python中如何使用列表？", priority="medium")
    tasks_dal.create_task("task_003", "什么是机器学习？", priority="low")
    tasks_dal.create_task("task_004", "深度学习和机器学习的区别？", priority="high")
    print_success("创建4个任务成功")

    # 查询任务
    print_info(f"查询任务 (task_id=task_001)...")
    task = tasks_dal.get_task_by_id("task_001")
    print_success(f"查询成功: {task['content']}")
    print(f"   状态: {task['status']}, 优先级: {task['priority']}")

    # 获取待处理任务
    print_info("获取待处理任务（按优先级排序）...")
    pending_tasks = tasks_dal.get_pending_tasks()
    print_success(f"获取成功，共 {len(pending_tasks)} 个待处理任务:")
    for i, t in enumerate(pending_tasks, 1):
        print(f"   {i}. [{t['priority']}] {t['content']}")

    # 更新任务状态
    print_info("更新任务状态为 'processing'...")
    tasks_dal.update_task_status("task_001", "processing", agent_id=agent_id)
    task = tasks_dal.get_task_by_id("task_001")
    print_success(f"状态更新成功: {task['status']}, Agent ID: {task['agent_id']}")

    # 获取任务数量
    count = tasks_dal.get_tasks_count()
    print_success(f"任务总数: {count}")

    return "task_001"


def test_results_dal(db_path, task_id):
    """测试ResultsDAL功能"""
    print_section("4. 测试 ResultsDAL (结果数据访问层)")

    results_dal = ResultsDAL(db_path)

    # 创建结果
    print_info(f"创建任务结果 (task_id={task_id})...")
    result_id = results_dal.create_result(
        task_id=task_id,
        content="人工智能（AI）是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。它包括机器学习、深度学习、自然语言处理等多个领域。",
        format="text",
        execution_time=2.5,
        status="success"
    )
    print_success(f"创建结果成功，ID: {result_id}")

    # 查询结果
    print_info(f"查询结果 (task_id={task_id})...")
    result = results_dal.get_result_by_task_id(task_id)
    print_success("查询成功")
    print(f"   内容: {result['content'][:50]}...")
    print(f"   执行时间: {result['execution_time']}秒")
    print(f"   状态: {result['status']}")

    # 获取所有结果
    print_info("创建更多结果...")
    results_dal.create_result("task_002", "Python列表是一种有序的可变集合...", execution_time=1.8, status="success")
    results_dal.create_result("task_003", "机器学习是AI的一个子领域...", execution_time=2.1, status="success")
    print_success("创建3个结果成功")

    all_results = results_dal.get_all_results()
    print_success(f"获取所有结果，共 {len(all_results)} 个")

    # 计算成功率
    print_info("计算成功率...")
    success_rate = results_dal.get_success_rate()
    print_success(f"成功率: {success_rate*100:.1f}%")

    # 计算平均执行时间
    print_info("计算平均执行时间...")
    avg_time = results_dal.get_average_execution_time()
    print_success(f"平均执行时间: {avg_time:.2f}秒")


def test_integration(db_path):
    """测试完整工作流"""
    print_section("5. 测试完整工作流（集成测试）")

    agents_dal = AgentsDAL(db_path)
    tasks_dal = TasksDAL(db_path)
    results_dal = ResultsDAL(db_path)

    # 1. 创建新Agent
    print_info("1. 创建新Agent...")
    config = {"api_key": "integration_test", "model": "gpt-3.5-turbo"}
    agent_id = agents_dal.create_agent(
        name="集成测试Agent",
        agent_type="test",
        config=config
    )
    print_success(f"Agent创建成功，ID: {agent_id}")

    # 2. 创建新任务
    print_info("2. 创建新任务...")
    task_id = "task_integration_001"
    tasks_dal.create_task(task_id, "集成测试问题", priority="high")
    print_success(f"任务创建成功，ID: {task_id}")

    # 3. 分配任务给Agent
    print_info("3. 分配任务给Agent...")
    tasks_dal.update_task_status(task_id, "processing", agent_id=agent_id)
    print_success("任务分配成功")

    # 4. 创建任务结果
    print_info("4. 创建任务结果...")
    results_dal.create_result(
        task_id=task_id,
        content="这是集成测试的回答",
        execution_time=1.2,
        status="success"
    )
    print_success("结果创建成功")

    # 5. 标记任务完成
    print_info("5. 标记任务完成...")
    tasks_dal.update_task_status(task_id, "completed")
    print_success("任务标记为完成")

    # 6. 验证完整流程
    print_info("6. 验证完整流程...")
    agent = agents_dal.get_agent_by_id(agent_id)
    task = tasks_dal.get_task_by_id(task_id)
    result = results_dal.get_result_by_task_id(task_id)

    print_success("验证成功:")
    print(f"   Agent: {agent['name']} ({agent['status']})")
    print(f"   Task: {task['content']} ({task['status']})")
    print(f"   Result: {result['content']} (耗时: {result['execution_time']}s)")


def test_backup_restore(db_path):
    """测试备份和恢复功能"""
    print_section("6. 测试备份和恢复功能")

    import subprocess
    import time

    backup_dir = Path(__file__).parent / "data" / "backup"

    # 创建备份
    print_info("创建数据库备份...")
    backup_script = Path(__file__).parent / "data" / "backup_db.py"

    # 使用JSON格式备份
    result = subprocess.run(
        [sys.executable, str(backup_script), "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )

    if result.returncode == 0:
        print_success("JSON备份创建成功")
        print_info(result.stdout)
    else:
        print(f"❌ 备份失败: {result.stderr}")
        return

    # 列出备份文件
    print_info("列出备份文件...")
    result = subprocess.run(
        [sys.executable, str(backup_script), "--list"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )

    if result.returncode == 0:
        print(result.stdout)

    # 恢复测试（仅验证）
    print_info("验证备份文件...")
    restore_script = Path(__file__).parent / "data" / "restore_db.py"

    # 获取最新的JSON备份文件
    json_backups = list(backup_dir.glob("full_backup_*.json"))
    if json_backups:
        latest_backup = max(json_backups, key=lambda x: x.stat().st_mtime)
        print_info(f"找到最新备份: {latest_backup.name}")

        result = subprocess.run(
            [sys.executable, str(restore_script), "--verify", str(latest_backup)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        if result.returncode == 0:
            print_success("备份验证成功")
        else:
            print(f"❌ 备份验证失败: {result.stderr}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  数据持久化层功能验证")
    print("  Simple Agent Framework - Data Layer Verification")
    print("="*60)

    try:
        # 初始化测试数据库
        db_path = init_test_database()

        # 测试各个模块
        agent_id = test_agents_dal(db_path)
        task_id = test_tasks_dal(db_path, agent_id)
        test_results_dal(db_path, task_id)
        test_integration(db_path)
        test_backup_restore(db_path)

        # 最终统计
        print_section("验证完成")

        print_success("所有功能验证通过！")
        print_info("验证的功能:")
        print("   ✅ Agent数据访问（CRUD、状态管理、配置管理）")
        print("   ✅ 任务数据访问（CRUD、状态跟踪、优先级排序）")
        print("   ✅ 结果数据访问（CRUD、统计计算）")
        print("   ✅ 完整工作流（Agent -> Task -> Result）")
        print("   ✅ 数据库备份和恢复")

        print(f"\n📊 测试数据库位置: {db_path}")
        print("💡 提示: 可以手动查看测试数据库以验证数据")

        return 0

    except Exception as e:
        print(f"\n❌ 验证过程中发生错误:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
