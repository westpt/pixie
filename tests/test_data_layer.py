"""
数据持久化层单元测试
测试DAL基类、AgentsDAL、TasksDAL、ResultsDAL的功能
"""

import unittest
import sqlite3
import tempfile
import shutil
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.dal import BaseDAL, DatabaseError, NotFoundError, DuplicateError
from data.agents_dal import AgentsDAL
from data.tasks_dal import TasksDAL
from data.results_dal import ResultsDAL
from data.models import (
    AGENTS_TABLE_SCHEMA,
    TASKS_TABLE_SCHEMA,
    RESULTS_TABLE_SCHEMA
)


class TestBaseDAL(unittest.TestCase):
    """测试BaseDAL基类"""

    def setUp(self):
        """测试前准备"""
        # 创建临时测试数据库
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = Path(self.temp_dir) / "test.db"
        self.dal = BaseDAL(str(self.test_db))

        # 创建测试表
        self.dal.execute_update("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value INTEGER
            )
        """)

    def tearDown(self):
        """测试后清理"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_insert_and_query(self):
        """测试插入和查询"""
        # 插入数据
        self.dal.execute_update(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("test", 100)
        )

        # 查询单条记录
        result = self.dal.execute_query(
            "SELECT * FROM test_table WHERE name = ?",
            ("test",)
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'test')
        self.assertEqual(result['value'], 100)

    def test_query_all(self):
        """测试查询所有记录"""
        # 插入多条数据
        for i in range(3):
            self.dal.execute_update(
                "INSERT INTO test_table (name, value) VALUES (?, ?)",
                (f"test{i}", i)
            )

        # 查询所有记录
        results = self.dal.execute_query(
            "SELECT * FROM test_table ORDER BY id",
            fetch_all=True
        )
        self.assertEqual(len(results), 3)

    def test_update(self):
        """测试更新操作"""
        # 插入数据
        self.dal.execute_update(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("test", 100)
        )

        # 更新数据
        affected = self.dal.execute_update(
            "UPDATE test_table SET value = ? WHERE name = ?",
            (200, "test")
        )
        self.assertEqual(affected, 1)

        # 验证更新
        result = self.dal.execute_query("SELECT * FROM test_table WHERE name = ?", ("test",))
        self.assertEqual(result['value'], 200)

    def test_delete(self):
        """测试删除操作"""
        # 插入数据
        self.dal.execute_update(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("test", 100)
        )

        # 删除数据
        affected = self.dal.execute_update(
            "DELETE FROM test_table WHERE name = ?",
            ("test",)
        )
        self.assertEqual(affected, 1)

        # 验证删除
        result = self.dal.execute_query("SELECT * FROM test_table WHERE name = ?", ("test",))
        self.assertIsNone(result)

    def test_table_exists(self):
        """测试表存在性检查"""
        self.assertTrue(self.dal.table_exists("test_table"))
        self.assertFalse(self.dal.table_exists("non_existent_table"))

    def test_get_row_count(self):
        """测试获取行数"""
        self.assertEqual(self.dal.get_row_count("test_table"), 0)

        # 插入数据
        for i in range(5):
            self.dal.execute_update(
                "INSERT INTO test_table (name, value) VALUES (?, ?)",
                (f"test{i}", i)
            )

        self.assertEqual(self.dal.get_row_count("test_table"), 5)

    def test_delete_all(self):
        """测试清空表"""
        # 插入数据
        for i in range(3):
            self.dal.execute_update(
                "INSERT INTO test_table (name, value) VALUES (?, ?)",
                (f"test{i}", i)
            )

        # 清空表
        affected = self.dal.delete_all("test_table")
        self.assertEqual(affected, 3)
        self.assertEqual(self.dal.get_row_count("test_table"), 0)

    def test_batch_execute(self):
        """测试批量执行"""
        data = [(f"test{i}", i) for i in range(5)]
        affected = self.dal.execute_batch(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            data
        )
        self.assertEqual(affected, 5)
        self.assertEqual(self.dal.get_row_count("test_table"), 5)

    def test_transaction(self):
        """测试事务"""
        queries = [
            ("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 1)),
            ("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 2)),
            ("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test3", 3)),
        ]

        total_affected = self.dal.execute_transaction(queries)
        self.assertEqual(total_affected, 3)
        self.assertEqual(self.dal.get_row_count("test_table"), 3)


class TestAgentsDAL(unittest.TestCase):
    """测试AgentsDAL"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = Path(self.temp_dir) / "test.db"
        self.dal = AgentsDAL(str(self.test_db))

        # 创建agents表
        conn = sqlite3.connect(str(self.test_db))
        conn.executescript(AGENTS_TABLE_SCHEMA)
        conn.commit()
        conn.close()

    def tearDown(self):
        """测试后清理"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_agent(self):
        """测试创建Agent"""
        config = {"api_key": "test_key", "model": "gpt-4"}
        agent_id = self.dal.create_agent("test_agent", "qa", config)
        self.assertGreater(agent_id, 0)

    def test_get_agent_by_id(self):
        """测试根据ID获取Agent"""
        config = {"api_key": "test_key"}
        agent_id = self.dal.create_agent("test_agent", "qa", config)

        agent = self.dal.get_agent_by_id(agent_id)
        self.assertIsNotNone(agent)
        self.assertEqual(agent['name'], "test_agent")
        self.assertEqual(agent['type'], "qa")
        self.assertEqual(agent['config'], config)

    def test_get_agent_by_name(self):
        """测试根据名称获取Agent"""
        config = {"api_key": "test_key"}
        self.dal.create_agent("test_agent", "qa", config)

        agent = self.dal.get_agent_by_name("test_agent")
        self.assertIsNotNone(agent)
        self.assertEqual(agent['name'], "test_agent")

    def test_get_all_agents(self):
        """测试获取所有Agent"""
        # 创建多个Agent
        for i in range(3):
            config = {"api_key": f"key{i}"}
            self.dal.create_agent(f"agent{i}", "qa", config)

        agents = self.dal.get_all_agents()
        self.assertEqual(len(agents), 3)

    def test_update_agent_status(self):
        """测试更新Agent状态"""
        config = {"api_key": "test_key"}
        agent_id = self.dal.create_agent("test_agent", "qa", config)

        success = self.dal.update_agent_status(agent_id, "running")
        self.assertTrue(success)

        agent = self.dal.get_agent_by_id(agent_id)
        self.assertEqual(agent['status'], "running")

    def test_update_agent_config(self):
        """测试更新Agent配置"""
        config = {"api_key": "old_key"}
        agent_id = self.dal.create_agent("test_agent", "qa", config)

        new_config = {"api_key": "new_key", "model": "gpt-4"}
        success = self.dal.update_agent_config(agent_id, new_config)
        self.assertTrue(success)

        agent = self.dal.get_agent_by_id(agent_id)
        self.assertEqual(agent['config'], new_config)

    def test_delete_agent(self):
        """测试删除Agent"""
        config = {"api_key": "test_key"}
        agent_id = self.dal.create_agent("test_agent", "qa", config)

        success = self.dal.delete_agent(agent_id)
        self.assertTrue(success)

        agent = self.dal.get_agent_by_id(agent_id)
        self.assertIsNone(agent)

    def test_get_agents_count(self):
        """测试获取Agent数量"""
        self.assertEqual(self.dal.get_agents_count(), 0)

        for i in range(3):
            config = {"api_key": f"key{i}"}
            self.dal.create_agent(f"agent{i}", "qa", config)

        self.assertEqual(self.dal.get_agents_count(), 3)

    def test_filter_agents_by_status(self):
        """测试按状态筛选Agent"""
        config = {"api_key": "test_key"}
        self.dal.create_agent("agent1", "qa", config, status="running")
        self.dal.create_agent("agent2", "qa", config, status="stopped")
        self.dal.create_agent("agent3", "qa", config, status="running")

        running_agents = self.dal.get_all_agents(status="running")
        self.assertEqual(len(running_agents), 2)


class TestTasksDAL(unittest.TestCase):
    """测试TasksDAL"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = Path(self.temp_dir) / "test.db"
        self.dal = TasksDAL(str(self.test_db))

        # 创建agents表（外键依赖）和tasks表
        conn = sqlite3.connect(str(self.test_db))
        conn.executescript(AGENTS_TABLE_SCHEMA)
        conn.executescript(TASKS_TABLE_SCHEMA)
        conn.commit()
        conn.close()

    def tearDown(self):
        """测试后清理"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_task(self):
        """测试创建任务"""
        task_id = self.dal.create_task("task_001", "测试任务内容")
        self.assertGreater(task_id, 0)

    def test_get_task_by_id(self):
        """测试根据ID获取任务"""
        internal_id = self.dal.create_task("task_001", "测试任务内容")

        task = self.dal.get_task_by_id("task_001")
        self.assertIsNotNone(task)
        self.assertEqual(task['task_id'], "task_001")
        self.assertEqual(task['content'], "测试任务内容")

    def test_get_all_tasks(self):
        """测试获取所有任务"""
        for i in range(3):
            self.dal.create_task(f"task_{i:03d}", f"任务{i}")

        tasks = self.dal.get_all_tasks()
        self.assertEqual(len(tasks), 3)

    def test_update_task_status(self):
        """测试更新任务状态"""
        self.dal.create_task("task_001", "测试任务")

        # 先创建agent（因为agent_id是外键）
        agents_dal = AgentsDAL(str(self.test_db))
        agent_id = agents_dal.create_agent("test_agent", "qa", {"api_key": "test"})

        success = self.dal.update_task_status("task_001", "processing", agent_id=agent_id)
        self.assertTrue(success)

        task = self.dal.get_task_by_id("task_001")
        self.assertEqual(task['status'], "processing")

    def test_get_pending_tasks(self):
        """测试获取待处理任务"""
        self.dal.create_task("task_001", "任务1", priority="high")
        self.dal.create_task("task_002", "任务2", priority="low")
        self.dal.create_task("task_003", "任务3", priority="medium")

        pending_tasks = self.dal.get_pending_tasks()
        self.assertEqual(len(pending_tasks), 3)
        # 验证优先级排序
        self.assertEqual(pending_tasks[0]['task_id'], "task_001")

    def test_get_tasks_count(self):
        """测试获取任务数量"""
        self.assertEqual(self.dal.get_tasks_count(), 0)

        for i in range(3):
            self.dal.create_task(f"task_{i:03d}", f"任务{i}")

        self.assertEqual(self.dal.get_tasks_count(), 3)

    def test_delete_task(self):
        """测试删除任务"""
        self.dal.create_task("task_001", "测试任务")

        success = self.dal.delete_task("task_001")
        self.assertTrue(success)

        task = self.dal.get_task_by_id("task_001")
        self.assertIsNone(task)


class TestResultsDAL(unittest.TestCase):
    """测试ResultsDAL"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = Path(self.temp_dir) / "test.db"
        self.dal = ResultsDAL(str(self.test_db))

        # 创建所有依赖表
        conn = sqlite3.connect(str(self.test_db))
        conn.executescript(AGENTS_TABLE_SCHEMA)
        conn.executescript(TASKS_TABLE_SCHEMA)
        conn.executescript(RESULTS_TABLE_SCHEMA)
        conn.commit()
        conn.close()

    def tearDown(self):
        """测试后清理"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_result(self):
        """测试创建结果"""
        # 先创建对应的task（外键约束）
        tasks_dal = TasksDAL(str(self.test_db))
        tasks_dal.create_task("task_001", "测试任务")

        result_id = self.dal.create_result("task_001", "测试结果", execution_time=1.5)
        self.assertGreater(result_id, 0)

    def test_get_result_by_task_id(self):
        """测试根据任务ID获取结果"""
        # 先创建对应的task
        tasks_dal = TasksDAL(str(self.test_db))
        tasks_dal.create_task("task_001", "测试任务")

        self.dal.create_result("task_001", "测试结果")

        result = self.dal.get_result_by_task_id("task_001")
        self.assertIsNotNone(result)
        self.assertEqual(result['task_id'], "task_001")

    def test_get_all_results(self):
        """测试获取所有结果"""
        tasks_dal = TasksDAL(str(self.test_db))
        # 创建对应的tasks
        for i in range(3):
            tasks_dal.create_task(f"task_{i:03d}", f"任务{i}")

        for i in range(3):
            self.dal.create_result(f"task_{i:03d}", f"结果{i}")

        results = self.dal.get_all_results()
        self.assertEqual(len(results), 3)

    def test_get_success_rate(self):
        """测试获取成功率"""
        tasks_dal = TasksDAL(str(self.test_db))
        # 创建对应的tasks
        for i in range(3):
            tasks_dal.create_task(f"task_{i:03d}", f"任务{i}")

        self.dal.create_result("task_000", "结果1", status="success")
        self.dal.create_result("task_001", "结果2", status="success")
        self.dal.create_result("task_002", "结果3", status="failed")

        success_rate = self.dal.get_success_rate()
        self.assertAlmostEqual(success_rate, 2/3, places=2)

    def test_get_average_execution_time(self):
        """测试获取平均执行时间"""
        tasks_dal = TasksDAL(str(self.test_db))
        # 创建对应的tasks
        for i in range(3):
            tasks_dal.create_task(f"task_{i:03d}", f"任务{i}")

        self.dal.create_result("task_000", "结果1", execution_time=1.0)
        self.dal.create_result("task_001", "结果2", execution_time=2.0)
        self.dal.create_result("task_002", "结果3", execution_time=3.0)

        avg_time = self.dal.get_average_execution_time()
        self.assertAlmostEqual(avg_time, 2.0, places=1)

    def test_get_results_count(self):
        """测试获取结果数量"""
        self.assertEqual(self.dal.get_results_count(), 0)

        tasks_dal = TasksDAL(str(self.test_db))
        # 创建对应的tasks
        for i in range(3):
            tasks_dal.create_task(f"task_{i:03d}", f"任务{i}")

        for i in range(3):
            self.dal.create_result(f"task_{i:03d}", f"结果{i}")

        self.assertEqual(self.dal.get_results_count(), 3)

    def test_delete_result_by_task_id(self):
        """测试根据任务ID删除结果"""
        tasks_dal = TasksDAL(str(self.test_db))
        tasks_dal.create_task("task_001", "测试任务")

        self.dal.create_result("task_001", "测试结果")

        success = self.dal.delete_result_by_task_id("task_001")
        self.assertTrue(success)

        result = self.dal.get_result_by_task_id("task_001")
        self.assertIsNone(result)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = Path(self.temp_dir) / "test.db"

        # 创建所有表
        conn = sqlite3.connect(str(self.test_db))
        conn.executescript(AGENTS_TABLE_SCHEMA)
        conn.executescript(TASKS_TABLE_SCHEMA)
        conn.executescript(RESULTS_TABLE_SCHEMA)
        conn.commit()
        conn.close()

        # 初始化DAL
        self.agents_dal = AgentsDAL(str(self.test_db))
        self.tasks_dal = TasksDAL(str(self.test_db))
        self.results_dal = ResultsDAL(str(self.test_db))

    def tearDown(self):
        """测试后清理"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_complete_workflow(self):
        """测试完整工作流：创建Agent -> 创建任务 -> 处理 -> 返回结果"""
        # 1. 创建Agent
        config = {"api_key": "test_key", "model": "gpt-4"}
        agent_id = self.agents_dal.create_agent("test_agent", "qa", config)

        # 2. 创建任务
        task_id = "task_001"
        self.tasks_dal.create_task(task_id, "测试问题")

        # 3. 更新任务状态为处理中
        self.tasks_dal.update_task_status(task_id, "processing", agent_id=agent_id)

        # 4. 创建结果
        self.results_dal.create_result(task_id, "测试答案", execution_time=1.5)

        # 5. 更新任务状态为完成
        self.tasks_dal.update_task_status(task_id, "completed")

        # 验证
        agent = self.agents_dal.get_agent_by_id(agent_id)
        self.assertEqual(agent['name'], "test_agent")

        task = self.tasks_dal.get_task_by_id(task_id)
        self.assertEqual(task['status'], "completed")

        result = self.results_dal.get_result_by_task_id(task_id)
        self.assertEqual(result['content'], "测试答案")


if __name__ == '__main__':
    unittest.main()
