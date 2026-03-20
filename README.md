# AI Agent Platform - 企业级 AI Agent 协同平台 MVP

一个基于 Python 的企业级 AI Agent 协同平台，支持多 Agent 协同、任务调度、角色管理等核心功能。

## 项目特点

- **分层架构设计**：CLI 和 Web 共享核心业务逻辑层
- **多 Agent 协同**：支持 Agent 注册、管理、状态监控
- **任务调度系统**：智能任务分配、优先级管理、队列管理
- **角色权限管理**：Agent 角色映射、技能管理、岗位信息
- **双模式交互**：支持 CLI 命令行和 Web 界面
- **数据持久化**：SQLite 数据库，完整的数据访问层
- **结构化日志**：JSON 格式日志，支持 Agent 和任务上下文

## 技术栈

- **后端**：Python 3.8+、Flask
- **数据库**：SQLite
- **配置**：YAML
- **大模型**：支持 OpenAI API、智谱 AI API
- **前端**：HTML + CSS + JavaScript
- **日志**：结构化 JSON 日志

## 项目结构

```
02_code/
├── agent_core/              # Agent 核心层
│   ├── base_agent.py         # Agent 基础类
│   └── qa_agent.py          # QA 助手实现
├── data/                    # 数据访问层
│   ├── dal.py                # 基础 DAL
│   ├── agents_dal.py         # Agent 数据访问
│   ├── tasks_dal.py          # 任务数据访问
│   ├── results_dal.py        # 结果数据访问
│   ├── models.py             # 数据模型定义
│   ├── init_db.py            # 数据库初始化脚本
│   ├── backup_db.py          # 数据库备份脚本
│   └── restore_db.py         # 数据库恢复脚本
├── core/                    # 核心业务逻辑层（CLI 和 Web 共用）
│   ├── interfaces.py         # 业务接口定义
│   ├── agent_manager.py      # Agent 管理器
│   └── task_manager.py       # 任务管理器
├── cli/                     # CLI 命令行接口
│   ├── __init__.py
│   └── main.py               # CLI 主程序
├── web/                     # Web 前端
│   ├── static/                # 静态资源（CSS、JS）
│   └── templates/             # HTML 模板
├── config/                  # 配置文件
│   ├── templates/             # 配置模板
│   ├── agent_template.yaml     # Agent 配置模板
│   └── qa_agent_config.yaml  # Agent 配置
├── logs/                    # 日志目录
├── data/data/                # SQLite 数据库文件
├── app.py                    # Web API 主程序
├── logging_config.py         # 日志配置模块
├── requirements.txt           # Python 依赖
├── start_and_test.sh         # 启动脚本
├── run.sh                    # 运行脚本
└── README.md                # 项目说明
```

## 快速开始

### 1. 环境要求

- Python 3.8 或更高版本
- pip（Python 包管理工具）

### 2. 安装步骤

```bash
# 克隆项目
cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python data/init_db.py
```

### 3. 配置 Agent

```bash
# 复制配置模板
cp config/agent_template.yaml config/qa_agent_config.yaml

# 编辑配置文件，填写 API Key
vim config/qa_agent_config.yaml
```

配置示例：

```yaml
agent:
  name: "QA助手"
  type: "qa_assistant"

llm:
  provider: "openai"  # 或 "zhipu"
  api_key: "your-api-key-here"
  api_endpoint: "https://api.openai.com/v1/chat/completions"
  model: "gpt-3.5-turbo"
  timeout: 30
  max_retries: 3

logging:
  level: "INFO"
  file: "logs/agent.log"
```

### 4. 启动服务

**方式 1：使用 Web 界面**
```bash
# 启动 Web 服务
python app.py

# 服务启动后，访问 http://localhost:5000
```

**方式 2：使用 CLI 命令行**
```bash
# 启动 CLI
python -m cli.main
```

## 使用说明

### 1. Web 界面使用

1. 打开浏览器访问 http://localhost:5000
2. 在文本框中输入您的问题
3. 点击"提交"按钮
4. 等待 Agent 返回回答
5. 查看回答结果

**可用页面：**
- 对话页面：与 Agent 交互
- 任务历史：查看所有任务执行记录
- Agent 状态：查看 Agent 运行状态
- 统计信息：查看系统统计数据

### 2. CLI 命令行使用

启动 CLI 后，可以使用以下命令：

**Agent 管理：**
```
agent> list-agents [status|type]
    列出所有 Agent，可选过滤条件

agent> create-agent <name> [type]
    创建新 Agent
    例如: create-agent my-agent qa

agent> show-agent <agent-id>
    显示 Agent 详细信息

agent> delete-agent <agent-id>
    删除指定的 Agent
```

**任务管理：**
```
agent> list-tasks [status|type|priority]
    列出所有任务，可选过滤条件

agent> create-task <content> [type] [priority]
    创建新任务
    例如: create-task "分析销售数据" sync medium

agent> show-task <task-id>
    显示任务详细信息

agent> execute-task <task-id> [agent-id]
    执行任务，可选指定 Agent
```

**其他：**
```
agent> help        显示帮助信息
agent> exit        退出程序
```

### 3. RESTful API 调用

**健康检查：**
```bash
curl http://localhost:5000/api/health
```

**就绪检查：**
```bash
curl http://localhost:5000/api/ready
```

**创建任务：**
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"content":"你的问题"}'
```

**查看任务列表：**
```bash
curl http://localhost:5000/api/tasks?status=completed
```

**查看 Agent 列表：**
```bash
curl http://localhost:5000/api/agents
```

**获取统计数据：**
```bash
curl http://localhost:5000/api/stats
```

## 核心功能

### 1. 核心业务逻辑层

**AgentManager（Agent 管理器）**
- 注册新 Agent
- 查询 Agent 信息
- 列出所有 Agent（支持过滤）
- 更新 Agent 信息
- 删除 Agent
- 获取 Agent 状态
- 加载/卸载 Agent

**TaskManager（任务管理器）**
- 创建任务
- 查询任务信息
- 列出所有任务（支持过滤）
- 更新任务状态
- 执行任务
- 获取任务结果
- 任务拆解（简化版）

### 2. Agent 框架核心

**BaseAgent（Agent 基础类）**
- 生命周期管理：create、start、stop、restart、destroy
- 状态管理：未初始化、已创建、运行中、已停止、已销毁
- 任务处理接口：process_task(task)
- 日志配置和输出
- 状态转换验证

**QAAssistant（QA 助手）**
- 继承 BaseAgent
- 集成 LLM API（OpenAI、智谱 AI）
- 任务执行逻辑
- 对话历史管理

### 3. 数据访问层（DAL）

**功能特性：**
- 统一的 CRUD 接口
- 数据库连接池管理
- 事务支持
- 错误处理
- 批量操作

**数据库表：**
- `agents`：Agent 配置信息
- `tasks`：任务记录
- `results`：任务执行结果
- `roles`：角色定义
- `agent_roles`：Agent-角色映射
- `config_history`：配置历史

### 4. 日志系统

**日志配置模块（logging_config.py）：**
- 结构化 JSON 日志
- Agent 日志适配器（添加 agent_id 上下文）
- 任务日志适配器（添加 task_id 上下文）
- 支持日志文件轮转
- 日志级别控制

**使用示例：**
```python
from logging_config import setup_logging, get_agent_logger, get_task_logger

# 设置日志系统
logger = setup_logging(level='INFO', log_file='logs/app.log')

# 获取 Agent 日志记录器
agent_logger = get_agent_logger(logger, agent_id='agent-123')
agent_logger.info("Agent 处理任务")

# 获取任务日志记录器
task_logger = get_task_logger(logger, task_id='task-456', agent_id='agent-123')
task_logger.info("任务执行完成")
```

### 5. 数据库初始化

**init_db.py 脚本功能：**
- 创建所有数据库表
- 添加扩展字段（position、skills、department）
- 创建角色相关表（roles、agent_roles）
- 数据库验证
- 支持重置模式（--reset）

**使用方法：**
```bash
# 初始化数据库（如果已存在则跳过）
python data/init_db.py

# 重置数据库（删除后重新创建）
python data/init_db.py --reset

# 验证数据库完整性
python data/init_db.py --verify
```

### 6. 数据库备份和恢复

**backup_db.py 脚本功能：**
- 完整数据库备份（压缩/不压缩）
- JSON格式备份（所有表）
- 单表CSV格式备份
- 自动清理旧备份

**restore_db.py 脚本功能：**
- 从备份恢复数据库
- 验证备份文件完整性
- 支持选择性表恢复

**使用方法：**
```bash
# 完整备份（压缩）
python data/backup_db.py --full

# JSON格式备份
python data/backup_db.py --json

# 备份单个表（CSV）
python data/backup_db.py --table agents

# 列出所有备份
python data/backup_db.py --list

# 清理旧备份（保留7天）
python data/backup_db.py --cleanup 7

# 验证备份文件
python data/restore_db.py --verify data/backup/agent_backup_*.db

# 恢复数据库（谨慎使用）
python data/restore_db.py data/backup/agent_backup_*.db

# 恢复单个表
python data/restore_db.py --table data/backup/agents_*.csv agents
```

## 开发指南

### 创建自定义 Agent

```python
from agent_core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.my_property = config.get('my_property')
    
    def process_task(self, task):
        # 实现任务处理逻辑
        result = self._do_something(task.content)
        
        # 返回结果
        return {
            'content': result,
            'format': 'text',
            'status': 'success',
            'execution_time': 1.5
        }
    
    def _do_something(self, content):
        # 具体业务逻辑
        return f"处理结果：{content}"
```

### 使用核心业务逻辑层

```python
from core import AgentManager, TaskManager
from data import AgentsDAL, TasksDAL, ResultsDAL

# 初始化管理器
agents_dal = AgentsDAL()
tasks_dal = TasksDAL()
results_dal = ResultsDAL()

agent_manager = AgentManager(agents_dal)
task_manager = TaskManager(tasks_dal, results_dal, agent_manager)

# 使用 AgentManager
agent_id = agent_manager.register_agent(config)
agent = agent_manager.get_loaded_agent(agent_id)

# 使用 TaskManager
task_id = task_manager.create_task("你的问题")
result = task_manager.execute_task(task_id)
```

### 扩展数据访问层

```python
from data.dal import BaseDAL

class CustomDAL(BaseDAL):
    def __init__(self, db_path):
        super().__init__(db_path)
    
    def custom_query(self, params):
        # 自定义查询逻辑
        query = "SELECT * FROM table WHERE condition = ?"
        return self.execute_query(query, (params,))
```

## 测试

### 数据持久化层测试

**运行数据持久化层验证脚本：**
```bash
# 运行自动化验证脚本
python verify_data_layer.py
```

**验证脚本包含：**
- AgentsDAL功能测试（CRUD、状态管理、配置管理）
- TasksDAL功能测试（CRUD、状态跟踪、优先级排序）
- ResultsDAL功能测试（CRUD、统计计算）
- 完整工作流测试（Agent → Task → Result）
- 数据库备份和恢复测试

**运行单元测试：**
```bash
# 运行数据持久化层单元测试
python -m pytest tests/test_data_layer.py -v

# 运行所有单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 查看测试覆盖率
pytest tests/ --cov=. --cov-report=html
```

**测试结果：**
- 数据持久化层：33/33 测试通过（100%覆盖率）
- 所有CRUD操作正常
- 外键约束正确
- 事务处理正常
- 错误处理完善

## 部署

### 生产环境部署

1. **配置生产环境的数据库**
   - 使用 PostgreSQL 替代 SQLite
   - 配置数据库连接池
   - 配置数据备份

2. **配置反向代理（Nginx）**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   }
   ```

3. **配置 HTTPS 证书**
   - 申请 SSL 证书
   - 配置 Nginx HTTPS
   - 强制 HTTPS 重定向

4. **配置日志监控**
   - 集中化日志管理（ELK、Loki）
   - 日志告警配置
   - 日志保留策略

5. **配置自动备份**
   - 数据库定期备份
   - 配置文件版本控制
   - 日志文件归档

### Docker 部署（可选）

```bash
# 构建 Docker 镜像
docker build -t ai-agent-platform .

# 运行容器
docker run -p 5000:5000 ai-agent-platform
```

## 常见问题

### Q1: 如何切换大模型 API？

A: 编辑配置文件 `config/qa_agent_config.yaml`，修改 `llm.provider`、`llm.api_key` 和 `llm.model`。

### Q2: 如何查看日志？

A: 
- 结构化日志：`logs/agent_*.log`（JSON 格式）
- 应用日志：`logs/app.log`
- 使用 `tail -f logs/agent.log` 实时查看。

### Q3: 如何重置数据库？

A: 运行 `python data/init_db.py --reset` 命令，数据库将重新初始化。

### Q4: 如何备份恢复数据？

A: 
- 备份：`cp data/data/agent.db data/backup/agent.db`
- 恢复：`cp data/backup/agent.db data/data/agent.db`
- 使用数据访问层的备份方法

### Q5: CLI 和 Web 模式有什么区别？

A: 
- **CLI 模式**：适合脚本自动化、批量操作、开发调试
- **Web 模式**：适合可视化操作、人机交互、图形化界面

两者共享相同的核心业务逻辑层和数据访问层，确保功能一致性。

### Q6: 如何扩展数据模型？

A:
1. 在 `data/models.py` 中添加表结构 SQL
2. 在 `data/init_db.py` 中添加初始化代码
3. 在 `data/*_dal.py` 中实现数据访问方法
4. 运行 `python data/init_db.py --reset` 重建数据库

### Q7: 如何验证数据持久化层功能？

A: 运行自动化验证脚本：
```bash
python verify_data_layer.py
```

该脚本会测试：
- AgentsDAL的所有功能
- TasksDAL的所有功能
- ResultsDAL的所有功能
- 完整工作流（Agent → Task → Result）
- 数据库备份和恢复功能

### Q8: 数据持久化层的测试结果如何？

A: 当前测试结果：
- 测试覆盖率：33/33 测试通过（100%）
- 测试代码行数：618 行
- DAL代码行数：~1,600 行
- 所有CRUD操作正常
- 外键约束正确
- 事务处理正常
- 错误处理完善

### Q9: 备份文件存储在哪里？

A: 备份文件存储在 `data/backup/` 目录，包括：
- 完整数据库备份（.db 或 .db.gz）
- JSON格式备份（full_backup_*.json）
- CSV格式备份（table_name_*.csv）

可以使用 `python data/backup_db.py --list` 查看所有备份。

## 项目架构图

```
┌─────────────────────────────────────────────────┐
│           用户交互层                      │
├─────────────┬───────────────────────────┤
│  CLI       │        Web (Flask)        │
│  main.py   │        app.py              │
└──────┬──────┴─────────────┬─────────────┘
       │                    │
       └──────────┬─────────┘
                  │
┌─────────────────▼───────────────────────┐
│      核心业务逻辑层                    │
│  - AgentManager                      │
│  - TaskManager                       │
│  - 接口抽象 (IAgentManager, ITaskManager) │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          数据访问层                     │
│  - AgentsDAL, TasksDAL, ResultsDAL    │
│  - BaseDAL (基础 DAL)               │
│  - 统一 CRUD 接口                     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          SQLite 数据库                     │
│  - agents, tasks, results, roles        │
│  - agent_roles, config_history        │
└─────────────────────────────────────────┘
```

## 后续规划

- [ ] 支持多 Agent 协同（已完成）
- [ ] 支持任务拆解与智能调度（部分完成）
- [ ] 支持 PostgreSQL 数据库
- [ ] 支持 WebSocket 实时通信
- [ ] 支持分布式部署
- [ ] 支持 FastAPI 迁移
- [ ] 支持向量数据库集成（ChromaDB）
- [ ] 支持流程编排
- [ ] 支持价值交付跟踪

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
