"""
主应用程序
Flask Web API + Agent管理
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data import AgentsDAL, TasksDAL, ResultsDAL
from agent_core import QAAssistant
from data.dal import BaseDAL

# 创建Flask应用
app = Flask(__name__)

# 全局变量
agent_dal = None
task_dal = None
result_dal = None
current_agent = None

# 数据库路径
DB_PATH = project_root / "data" / "agent.db"

def init_dal():
    """初始化数据访问层"""
    global agent_dal, task_dal, result_dal
    
    agent_dal = AgentsDAL(str(DB_PATH))
    task_dal = TasksDAL(str(DB_PATH))
    result_dal = ResultsDAL(str(DB_PATH))
    
    print(f"数据库初始化成功：{DB_PATH}")

def load_agent():
    """加载Agent配置"""
    global current_agent
    
    config_path = project_root / "config" / "qa_agent_config.yaml"
    
    if not config_path.exists():
        print(f"错误：配置文件不存在：{config_path}")
        print("请先创建Agent配置文件")
        return False
    
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 创建QA助手Agent
    try:
        current_agent = QAAssistant(config)
        
        # 保存Agent信息到数据库
        agent_id = agent_dal.create_agent(
            name=config.get('agent', {}).get('name', 'QA助手'),
            agent_type='qa_assistant',
            config=config,
            status='running'
        )
        
        print(f"Agent加载成功：{current_agent.name}")
        return True
        
    except Exception as e:
        print(f"错误：Agent加载失败 - {str(e)}")
        return False

# Flask路由

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'agent': {
            'name': current_agent.name if current_agent else None,
            'status': current_agent.get_status() if current_agent else 'not_loaded'
        } if current_agent else {}
    })

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建任务"""
    if not current_agent:
        return jsonify({'error': 'Agent未加载'}), 500
    
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': '任务内容不能为空'}), 400
    
    # 生成任务ID
    import uuid
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task_internal_id = task_dal.create_task(
        task_id=task_id,
        content=content,
        task_type='sync',
        priority='medium',
        status='pending'
    )
    
    # 更新任务状态为处理中
    task_dal.update_task_status(task_id, 'processing', current_agent.agent_id)
    
    # 处理任务
    task_data = {
        'task_id': task_id,
        'content': content,
        'task_type': 'sync'
    }
    result_data = current_agent.process_task(task_data)
    
    # 保存结果
    result_dal.create_result(
        task_id=task_id,
        content=result_data.get('content', ''),
        format=result_data.get('format', 'text'),
        execution_time=result_data.get('execution_time'),
        status=result_data.get('status', 'success')
    )
    
    # 更新任务状态
    task_dal.update_task_status(
        task_id,
        'completed' if result_data.get('status') == 'success' else 'failed'
    )
    
    return jsonify({
        'task_id': task_id,
        'status': 'completed' if result_data.get('status') == 'success' else 'failed',
        'result': result_data
    })

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    task = task_dal.get_task_by_id(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    # 获取结果
    result = result_dal.get_result_by_task_id(task_id)
    
    return jsonify({
        'task': task,
        'result': result
    })

@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """获取任务列表"""
    status = request.args.get('status')
    limit = request.args.get('limit', type=int, default=20)
    offset = request.args.get('offset', type=int, default=0)
    
    tasks = task_dal.get_all_tasks(
        status=status,
        limit=limit,
        offset=offset
    )
    
    return jsonify({
        'tasks': tasks,
        'count': len(tasks)
    })

@app.route('/api/agents/status', methods=['GET'])
def get_agent_status():
    """获取Agent状态"""
    if not current_agent:
        return jsonify({'error': 'Agent未加载'}), 500
    
    return jsonify({
        'agent_id': current_agent.agent_id,
        'name': current_agent.name,
        'type': current_agent.agent_type,
        'status': current_agent.get_status(),
        'info': current_agent.get_info()
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    total_tasks = task_dal.get_tasks_count()
    pending_tasks = task_dal.get_tasks_count(status='pending')
    completed_tasks = task_dal.get_tasks_count(status='completed')
    failed_tasks = task_dal.get_tasks_count(status='failed')
    
    success_rate = result_dal.get_success_rate()
    avg_execution_time = result_dal.get_average_execution_time()
    
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

@app.route('/api/conversation/clear', methods=['POST'])
def clear_conversation():
    """清空对话历史"""
    if not current_agent:
        return jsonify({'error': 'Agent未加载'}), 500
    
    current_agent.clear_conversation_history()
    
    return jsonify({
        'status': 'success',
        'message': '对话历史已清空'
    })

@app.route('/api/conversation/history', methods=['GET'])
def get_conversation_history():
    """获取对话历史"""
    if not current_agent:
        return jsonify({'error': 'Agent未加载'}), 500
    
    history = current_agent.get_conversation_history()
    
    return jsonify({
        'history': history
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
    
    # 初始化数据库
    init_dal()
    
    # 加载Agent
    if load_agent():
        print("\n✓ Agent加载成功")
        print(f"✓ Web服务启动：http://0.0.0.0:5000")
        print("\n按 Ctrl+C 停止服务\n")
        
        # 启动Flask应用
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("\n✗ Agent加载失败")
        print("请检查配置文件后重试")
        sys.exit(1)

