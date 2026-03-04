# AI Agent Framework - 轻量级单Agent框架

一个基于Python的轻量级AI Agent框架，支持Agent的创建、配置、任务处理与人机交互。本框架聚焦核心功能，不依赖LangGraph等复杂框架，便于快速验证Agent概念。

## 项目特点

- **轻量级设计**：纯Python实现，不依赖LangGraph、AutoGen等复杂框架
- **简单易用**：清晰的代码结构，易于理解和扩展
- **单Agent支持**：聚焦单Agent场景，快速验证核心功能
- **Web界面**：提供简洁的Web界面，支持人机交互
- **配置灵活**：支持YAML配置文件，热加载配置

## 技术栈

- **后端**：Python 3.8+、Flask
- **数据库**：SQLite
- **配置**：YAML
- **大模型**：支持OpenAI API、通义千问API
- **前端**：HTML + CSS + JavaScript

## 项目结构

```
02_code/
├── agent_core/          # Agent核心层
├── task_manager/       # 任务管理层
├── api/               # Web API层
├── web/               # Web前端
│   ├── static/         # 静态资源（CSS、JS）
│   └── templates/      # HTML模板
├── config/             # 配置文件
│   ├── templates/      # 配置模板
│   └── *.yaml         # Agent配置
├── data/              # 数据目录
│   ├── *.db           # SQLite数据库
│   └── backup/        # 数据库备份
├── logs/              # 日志目录
├── tests/             # 测试代码
├── requirements.txt     # Python依赖
├── README.md          # 项目说明
└── .gitignore        # Git忽略配置
```

## 快速开始

### 1. 环境要求

- Python 3.8 或更高版本
- pip（Python包管理工具）

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
python init_db.py
```

### 3. 配置Agent

```bash
# 复制配置模板
cp config/templates/agent_template.yaml config/qa_agent_config.yaml

# 编辑配置文件，填写API Key
vim config/qa_agent_config.yaml
```

配置示例：

```yaml
agent:
  name: "QA助手"
  type: "qa_assistant"
  
llm:
  provider: "openai"  # 或 "qwen"
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

```bash
# 启动Web服务
python app.py

# 服务启动后，访问 http://localhost:5000
```

## 使用说明

### 1. Web界面使用

1. 打开浏览器访问 http://localhost:5000
2. 在文本框中输入您的问题
3. 点击"提交"按钮
4. 等待Agent返回回答
5. 查看回答结果，支持复制和下载

### 2. 查看任务历史

1. 点击"任务历史"标签
2. 查看所有任务的执行记录
3. 支持按状态、按时间筛选

### 3. 查看Agent状态

1. 点击"Agent状态"标签
2. 查看Agent的运行状态
3. 查看当前处理任务和队列长度

### 4. 管理配置

1. 点击"配置管理"标签
2. 在线修改Agent配置
3. 点击"保存"应用新配置

## 核心功能

### 1. Agent框架核心

- `BaseAgent`：Agent基础类，封装通用属性与行为
- 生命周期管理：create、start、stop、restart、destroy
- 状态管理：未初始化、已创建、运行中、已停止、已销毁
- 任务处理接口：process_task(task)

### 2. 任务管理

- 任务队列：FIFO队列管理
- 任务分配：智能分配给Agent
- 状态跟踪：待处理、处理中、已完成、失败
- 超时处理：自动终止超时任务
- 重试机制：自动重试失败任务

### 3. 数据持久化

- SQLite数据库：轻量级数据存储
- 三表设计：agents表、tasks表、results表
- 数据访问层（DAL）：封装数据库操作
- 备份恢复：支持数据库备份与恢复

### 4. 配置管理

- YAML配置文件：易于编辑和维护
- 配置验证：必填字段、数据类型、API连通性
- 配置历史：记录配置修改，支持版本回退
- 热加载：在线修改配置，无需重启

### 5. 人机交互

- Web界面：简洁易用的操作界面
- 异步请求：AJAX实现，无需刷新页面
- 实时更新：任务状态实时显示
- 响应式设计：支持多种设备

## 开发指南

### 创建自定义Agent

```python
from agent_core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.my_property = config.get('my_property')
    
    def process_task(self, task):
        # 实现任务处理逻辑
        result = self._do_something(task.content)
        return result
    
    def _do_something(self, content):
        # 具体业务逻辑
        return f"处理结果：{content}"
```

### 扩展任务处理逻辑

```python
from task_manager.task_queue import TaskQueue
from agent_core.base_agent import BaseAgent

class CustomTaskQueue(TaskQueue):
    def assign_task(self, agent, task):
        # 自定义任务分配逻辑
        if task.priority == 'high':
            return super().assign_task(agent, task)
        else:
            # 特殊处理
            return self._custom_assign(agent, task)
```

## 测试

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 查看测试覆盖率
pytest tests/ --cov=. --cov-report=html
```

## 部署

### Docker部署（可选）

```bash
# 构建Docker镜像
docker build -t ai-agent-framework .

# 运行容器
docker run -p 5000:5000 ai-agent-framework
```

### 生产环境部署

1. 配置生产环境的数据库（PostgreSQL）
2. 配置反向代理（Nginx）
3. 配置HTTPS证书
4. 配置日志监控
5. 配置自动备份

## 常见问题

### Q1: 如何切换大模型API？

A: 编辑配置文件 `config/qa_agent_config.yaml`，修改 `llm.provider` 和 `llm.api_key`。

### Q2: 如何查看日志？

A: 日志文件位于 `logs/agent.log`，使用 `tail -f logs/agent.log` 实时查看。

### Q3: 如何重置数据库？

A: 运行 `python init_db.py --reset` 命令，数据库将重新初始化。

### Q4: 如何备份数据？

A: 运行 `python backup_db.py`，数据库备份将保存到 `data/backup/` 目录。

## 后续规划

- [ ] 支持多Agent协同
- [ ] 支持任务拆解与智能调度
- [ ] 支持LangGraph集成
- [ ] 支持WebSocket实时通信
- [ ] 支持分布式部署

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue。
