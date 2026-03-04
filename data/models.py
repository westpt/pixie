"""
数据模型定义
定义agents表、tasks表、results表的SQL模型
"""

# 数据库表结构设计
#
# 1. agents表：存储Agent配置信息
# 2. tasks表：存储任务记录
# 3. results表：存储任务执行结果

AGENTS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    config TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
"""

TASKS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    task_type TEXT NOT NULL DEFAULT 'sync',
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'pending',
    agent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
"""

RESULTS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    content TEXT,
    format TEXT NOT NULL DEFAULT 'text',
    execution_time REAL,
    status TEXT NOT NULL DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_results_task_id ON results(task_id);
CREATE INDEX IF NOT EXISTS idx_results_status ON results(status);
CREATE INDEX IF NOT EXISTS idx_results_created_at ON results(created_at);
"""

# 配置历史表（可选，用于Agent配置版本管理）
CONFIG_HISTORY_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS config_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    config TEXT NOT NULL,
    version INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_config_history_agent_id ON config_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_config_history_version ON config_history(agent_id, version);
"""

# 状态枚举
#
# Agent状态：
# - 'uninitialized': 未初始化
# - 'created': 已创建
# - 'running': 运行中
# - 'stopped': 已停止
# - 'destroyed': 已销毁
#
# 任务状态：
# - 'pending': 待处理
# - 'processing': 处理中
# - 'completed': 已完成
# - 'failed': 失败
#
# 结果状态：
# - 'success': 成功
# - 'failed': 失败

# 任务优先级
PRIORITY_LEVELS = ['low', 'medium', 'high']

# 任务类型
TASK_TYPES = ['sync', 'async']

# 结果格式
RESULT_FORMATS = ['text', 'json', 'html', 'markdown']

