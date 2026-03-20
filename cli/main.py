"""
CLI 主程序
提供命令行操作界面
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import AgentManager, TaskManager
from data import AgentsDAL, TasksDAL, ResultsDAL, BaseDAL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLIInterface:
    """CLI 接口"""

    def __init__(self):
        """初始化 CLI"""
        # 初始化数据访问层
        agents_dal = AgentsDAL()
        tasks_dal = TasksDAL()
        results_dal = ResultsDAL()

        # 初始化管理器
        self.agent_manager = AgentManager(agents_dal)
        self.task_manager = TaskManager(tasks_dal, results_dal, self.agent_manager)

        logger.info("CLI 初始化成功")

    def run(self):
        """运行 CLI"""
        print("""
╔════════════════════════════════════════════════════════════╗
║           AI Agent Platform - 命令行界面                      ║
╚════════════════════════════════════════════════════════════╝

可用命令:
  help              显示帮助信息
  list-agents       列出所有 Agent
  create-agent      创建新 Agent
  show-agent        显示 Agent 详情
  delete-agent      删除 Agent
  list-tasks        列出所有任务
  create-task       创建新任务
  show-task         显示任务详情
  execute-task      执行任务
  exit              退出程序
""")

        while True:
            try:
                # 读取用户输入
                cmd = input("\nagent> ").strip()

                if not cmd:
                    continue

                # 解析命令
                parts = cmd.split()
                command = parts[0].lower()
                args = parts[1:]

                # 执行命令
                if command == 'help':
                    self.show_help()
                elif command == 'list-agents':
                    self.list_agents(args)
                elif command == 'create-agent':
                    self.create_agent(args)
                elif command == 'show-agent':
                    self.show_agent(args)
                elif command == 'delete-agent':
                    self.delete_agent(args)
                elif command == 'list-tasks':
                    self.list_tasks(args)
                elif command == 'create-task':
                    self.create_task(args)
                elif command == 'show-task':
                    self.show_task(args)
                elif command == 'execute-task':
                    self.execute_task(args)
                elif command == 'exit':
                    print("再见！")
                    break
                else:
                    print(f"未知命令: {command}")
                    print("输入 'help' 查看可用命令")

            except KeyboardInterrupt:
                print("\n\n程序已中断")
                break
            except Exception as e:
                logger.error(f"执行命令时出错: {str(e)}")
                print(f"错误: {str(e)}")

    def show_help(self):
        """显示帮助信息"""
        print("""
命令帮助:

Agent 管理:
  list-agents [status|type]
    列出所有 Agent，可选过滤条件

  create-agent <name> [type]
    创建新 Agent
    例如: create-agent my-agent qa

  show-agent <agent-id>
    显示 Agent 详细信息

  delete-agent <agent-id>
    删除指定的 Agent

任务管理:
  list-tasks [status|type|priority]
    列出所有任务，可选过滤条件

  create-task <content> [type] [priority]
    创建新任务
    例如: create-task "分析销售数据" sync medium

  show-task <task-id>
    显示任务详细信息

  execute-task <task-id> [agent-id]
    执行任务，可选指定 Agent

其他:
  help        显示此帮助信息
  exit        退出程序
""")

    def list_agents(self, args: list):
        """列出所有 Agent"""
        filters = {}
        if args:
            if args[0] in ['created', 'running', 'stopped']:
                filters['status'] = args[0]
            else:
                filters['type'] = args[0]

        agents = self.agent_manager.list_agents(filters)

        if not agents:
            print("没有找到 Agent")
            return

        print(f"\n找到 {len(agents)} 个 Agent:\n")
        print(f"{'ID':<8} {'名称':<20} {'类型':<10} {'状态':<10}")
        print("-" * 50)
        for agent in agents:
            agent_id_short = agent['agent_id'][:8]
            print(f"{agent_id_short:<8} {agent['name']:<20} {agent['type']:<10} {agent['status']:<10}")

    def create_agent(self, args: list):
        """创建新 Agent"""
        if not args:
            print("错误: 请提供 Agent 名称")
            print("用法: create-agent <name> [type]")
            return

        name = args[0]
        agent_type = args[1] if len(args) > 1 else 'base'

        # 获取配置文件路径
        config_path = project_root / "config" / "qa_agent_config.yaml"

        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 更新配置
        config['name'] = name
        config['type'] = agent_type

        try:
            agent_id = self.agent_manager.register_agent(config)
            print(f"✓ Agent 创建成功")
            print(f"  ID: {agent_id}")
            print(f"  名称: {name}")
            print(f"  类型: {agent_type}")
        except Exception as e:
            print(f"✗ Agent 创建失败: {str(e)}")

    def show_agent(self, args: list):
        """显示 Agent 详情"""
        if not args:
            print("错误: 请提供 Agent ID")
            print("用法: show-agent <agent-id>")
            return

        agent_id = args[0]
        agent = self.agent_manager.get_agent(agent_id)

        if not agent:
            print(f"✗ Agent 不存在: {agent_id}")
            return

        print(f"\nAgent 信息:")
        print(f"  ID: {agent['agent_id']}")
        print(f"  名称: {agent['name']}")
        print(f"  类型: {agent['type']}")
        print(f"  状态: {agent['status']}")
        print(f"  创建时间: {agent['created_at']}")

        # 获取实时状态
        status = self.agent_manager.get_agent_status(agent_id)
        if status:
            print(f"\n运行时状态:")
            print(f"  状态: {status['status']}")
            print(f"  已处理任务: {status['processed_count']}")
            print(f"  错误次数: {status['error_count']}")
            if status['current_task']:
                print(f"  当前任务: {status['current_task']}")

    def delete_agent(self, args: list):
        """删除 Agent"""
        if not args:
            print("错误: 请提供 Agent ID")
            print("用法: delete-agent <agent-id>")
            return

        agent_id = args[0]

        # 确认删除
        confirm = input(f"确定要删除 Agent {agent_id} 吗? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消删除")
            return

        if self.agent_manager.delete_agent(agent_id):
            print(f"✓ Agent 删除成功: {agent_id}")
        else:
            print(f"✗ Agent 删除失败: {agent_id}")

    def list_tasks(self, args: list):
        """列出所有任务"""
        filters = {}
        if args:
            if args[0] in ['pending', 'processing', 'completed', 'failed']:
                filters['status'] = args[0]
            elif args[0] in ['sync', 'async']:
                filters['task_type'] = args[0]
            elif args[0] in ['low', 'medium', 'high']:
                filters['priority'] = args[0]

        tasks = self.task_manager.list_tasks(filters)

        if not tasks:
            print("没有找到任务")
            return

        print(f"\n找到 {len(tasks)} 个任务:\n")
        print(f"{'ID':<8} {'内容':<30} {'状态':<10} {'优先级':<8}")
        print("-" * 60)
        for task in tasks:
            task_id_short = task['task_id'][:8]
            content_short = task['content'][:30]
            print(f"{task_id_short:<8} {content_short:<30} {task['status']:<10} {task['priority']:<8}")

    def create_task(self, args: list):
        """创建新任务"""
        if not args:
            print("错误: 请提供任务内容")
            print("用法: create-task <content> [type] [priority]")
            return

        content = args[0]
        task_type = args[1] if len(args) > 1 else 'sync'
        priority = args[2] if len(args) > 2 else 'medium'

        try:
            task_id = self.task_manager.create_task(content, task_type, priority)
            print(f"✓ 任务创建成功")
            print(f"  ID: {task_id}")
            print(f"  内容: {content}")
            print(f"  类型: {task_type}")
            print(f"  优先级: {priority}")
        except Exception as e:
            print(f"✗ 任务创建失败: {str(e)}")

    def show_task(self, args: list):
        """显示任务详情"""
        if not args:
            print("错误: 请提供任务 ID")
            print("用法: show-task <task-id>")
            return

        task_id = args[0]
        task = self.task_manager.get_task(task_id)

        if not task:
            print(f"✗ 任务不存在: {task_id}")
            return

        print(f"\n任务信息:")
        print(f"  ID: {task['task_id']}")
        print(f"  内容: {task['content']}")
        print(f"  类型: {task['task_type']}")
        print(f"  优先级: {task['priority']}")
        print(f"  状态: {task['status']}")
        print(f"  创建时间: {task['created_at']}")
        if task['assigned_agent_id']:
            print(f"  分配 Agent: {task['assigned_agent_id'][:8]}")
        if task['completed_at']:
            print(f"  完成时间: {task['completed_at']}")

        # 获取任务结果
        result = self.task_manager.get_task_result(task_id)
        if result:
            print(f"\n执行结果:")
            print(f"  状态: {result['status']}")
            print(f"  执行时间: {result['execution_time']}s")
            print(f"  内容: {result['content']}")

    def execute_task(self, args: list):
        """执行任务"""
        if not args:
            print("错误: 请提供任务 ID")
            print("用法: execute-task <task-id> [agent-id]")
            return

        task_id = args[0]
        agent_id = args[1] if len(args) > 1 else None

        print(f"\n执行任务: {task_id}")
        print("请稍候...")

        result = self.task_manager.execute_task(task_id, agent_id)

        if result['status'] == 'completed':
            print(f"\n✓ 任务执行成功")
            print(f"  ID: {result['task_id']}")
            print(f"  结果: {result['result'].get('content', '')}")
        else:
            print(f"\n✗ 任务执行失败")
            print(f"  ID: {result['task_id']}")
            print(f"  错误: {result['result'].get('content', '')}")


def main():
    """主函数"""
    try:
        cli = CLIInterface()
        cli.run()
    except Exception as e:
        logger.error(f"CLI 启动失败: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
