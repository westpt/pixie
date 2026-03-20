"""
主应用程序
Flask Web API + Agent管理
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from data import AgentsDAL, TasksDAL, ResultsDAL
from core import AgentManager, TaskManager

# 创建Flask应用，指定模板目录和静态文件目录
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

# 全局变量
agent_manager = None
task_manager = None
current_agent_id = None

# 数据库路径
DB_PATH = project_root / "data" / "data" / "agent.db"

def init_managers():
    """初始化管理器"""
    global agent_manager, task_manager

    # 初始化数据访问层
    agents_dal = AgentsDAL(str(DB_PATH))
    tasks_dal = TasksDAL(str(DB_PATH))
    results_dal = ResultsDAL(str(DB_PATH))

    # 初始化管理器
    agent_manager = AgentManager(agents_dal)
    task_manager = TaskManager(tasks_dal, results_dal, agent_manager)

    logger.info(f"管理器初始化成功，数据库：{DB_PATH}")

def load_default_agent():
    """加载默认Agent"""
    global current_agent_id

    config_path = project_root / "config" / "qa_agent_config.yaml"

    if not config_path.exists():
        logger.error(f"配置文件不存在：{config_path}")
        return False

    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 检查是否已存在默认Agent
    agents = agent_manager.list_agents()
    default_agent = None
    for agent in agents:
        if agent['name'] == config.get('agent', {}).get('name', 'QA助手'):
            default_agent = agent
            break

    if default_agent:
        # 已存在，加载它
        current_agent_id = default_agent['agent_id']
        agent_manager.load_agent(current_agent_id)
        logger.info(f"默认Agent已加载：{default_agent['name']} (ID: {current_agent_id})")
    else:
        # 不存在，创建新的
        try:
            current_agent_id = agent_manager.register_agent(config)
            agent_manager.load_agent(current_agent_id)
            logger.info(f"默认Agent创建并加载成功：{config.get('agent', {}).get('name', 'QA助手')}")
        except Exception as e:
            logger.error(f"默认Agent加载失败：{str(e)}")
            return False

    return True

# Flask路由

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """健康检查"""
    agent_status = None
    if current_agent_id:
        agent_status = agent_manager.get_agent_status(current_agent_id)

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'agent': agent_status
    })

@app.route('/api/ready')
def ready():
    """就绪检查"""
    return jsonify({
        'status': 'ready',
        'timestamp': datetime.now().isoformat(),
        'manager': {
            'agent_manager': agent_manager is not None,
            'task_manager': task_manager is not None
        }
    })

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建任务"""
    if not current_agent_id:
        return jsonify({'error': 'Agent未加载'}), 500

    data = request.json
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': '任务内容不能为空'}), 400

    # 创建任务
    task_id = task_manager.create_task(content)

    # 执行任务
    result = task_manager.execute_task(task_id, current_agent_id)

    return jsonify(result)

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    task = task_manager.get_task(task_id)

    if not task:
        return jsonify({'error': '任务不存在'}), 404

    # 获取结果
    result = task_manager.get_task_result(task_id)

    return jsonify({
        'task': task,
        'result': result
    })

@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """获取任务列表"""
    status = request.args.get('status')

    filters = {}
    if status:
        filters['status'] = status

    tasks = task_manager.list_tasks(filters)

    return jsonify({
        'tasks': tasks,
        'count': len(tasks)
    })

@app.route('/api/agents', methods=['GET'])
def list_agents():
    """获取Agent列表"""
    filters = {}
    status = request.args.get('status')
    if status:
        filters['status'] = status

    agents = agent_manager.list_agents(filters)

    return jsonify({
        'agents': agents,
        'count': len(agents)
    })

@app.route('/api/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """获取Agent详情"""
    agent = agent_manager.get_agent(agent_id)

    if not agent:
        return jsonify({'error': 'Agent不存在'}), 404

    # 获取实时状态
    status = agent_manager.get_agent_status(agent_id)

    return jsonify({
        'agent': agent,
        'status': status
    })

@app.route('/api/agents/status', methods=['GET'])
def get_agent_status():
    """获取默认Agent状态"""
    if not current_agent_id:
        return jsonify({'error': 'Agent未加载'}), 500

    agent = agent_manager.get_agent(current_agent_id)
    status = agent_manager.get_agent_status(current_agent_id)

    return jsonify({
        'agent_id': current_agent_id,
        'name': agent['name'] if agent else None,
        'type': agent['type'] if agent else None,
        'status': status['status'] if status else 'not_loaded',
        'info': status
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    tasks = task_manager.list_tasks()

    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
    failed_tasks = len([t for t in tasks if t['status'] == 'failed'])
    pending_tasks = len([t for t in tasks if t['status'] == 'pending'])

    # 简单的成功率计算
    success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

    # 平均执行时间（简化版）
    avg_execution_time = 0.5  # 占位值

    return jsonify({
        'tasks': {
            'total': total_tasks,
            'pending': pending_tasks,
            'completed': completed_tasks,
            'failed': failed_tasks
        },
        'performance': {
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time
        }
    })

# 错误处理

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '资源不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("AI Agent Framework - 启动中...")
    print("=" * 50)

    # 初始化管理器
    init_managers()

    # 加载默认Agent
    if load_default_agent():
        print("\n✓ Agent加载成功")
        print(f"✓ Web服务启动：http://0.0.0.0:5000")
        print("\n按 Ctrl+C 停止服务\n")

        # 启动Flask应用
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("\n✗ Agent加载失败")
        print("请检查配置文件后重试")
        sys.exit(1)
