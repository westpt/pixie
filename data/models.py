"""
数据模型定义
定义agents表、tasks表、results表的SQL模型
"""

# 数据库表结构设计
#
# 1. agents表：存储Agent配置信息
# 2. tasks表：存储任务记录
# 3. results表：存储任务执行结果
#

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
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
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

# 新增：角色定义表（用于任务 3.11）
ROLES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    responsibilities TEXT,  -- 职责描述（JSON格式）
    permissions TEXT,       -- 权限配置（JSON格式）
    collaboration_rules TEXT, -- 协作规则（JSON格式）
    template_type TEXT DEFAULT 'custom',  -- 模板类型：default, custom
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
"""

# 新增：Agent-角色映射表（用于任务 3.12）
AGENT_ROLES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    department TEXT,           -- 所属部门
    skills TEXT,               -- 技能列表（JSON格式）
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE(agent_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_roles_agent_id ON agent_roles(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_roles_role_id ON agent_roles(role_id);
"""

# 新增：扩展 agents 表，添加岗位和技能字段
# 注意：这些 ALTER TABLE 语句在 init_db.py 中单独执行
AGENTS_EXTENDED_COLUMNS_SCHEMA = """
ALTER TABLE agents ADD COLUMN position TEXT;
ALTER TABLE agents ADD COLUMN skills TEXT;
ALTER TABLE agents ADD COLUMN department TEXT;
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
#
# 任务优先级
PRIORITY_LEVELS = ['low', 'medium', 'high']
#
# 任务类型
TASK_TYPES = ['sync', 'async']
#
# 结果格式
RESULT_FORMATS = ['text', 'json', 'html', 'markdown']
#
# 协作类型（用于角色定义）
COLLABORATION_TYPES = ['network', 'hierarchical', 'supervisor']
#
# 角色模板类型
ROLE_TEMPLATE_TYPES = ['default', 'custom']
