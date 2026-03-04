# 快速启动指南

## 问题说明

当前系统Python环境缺少Flask依赖，有两种解决方案：

### 方案1：使用系统Python（推荐）

如果您有管理员权限，可以使用系统Python直接安装依赖：

```bash
# 方法A：使用apt安装（推荐）
sudo apt update
sudo apt install python3-flask python3-yaml python3-requests

# 方法B：使用pip3系统安装
pip3 install --user flask pyyaml requests
```

然后直接启动：

```bash
python3 app.py
```

访问：http://localhost:5000

---

### 方案2：使用Jarvis虚拟环境

如果您已经配置了Jarvis环境，可以复制安装的包：

```bash
# 查看Jarvis环境已安装的包
/home/wstpt/01_AI/02_Agent/07_pixie/02_Jarvis/.venv/bin/pip3 list

# 启动服务时使用Jarvis的Python
/home/wstpt/01_AI/02_Agent/07_pixie/02_Jarvis/.venv/bin/python3 app.py
```

访问：http://localhost:5000

---

## 当前系统状态

✅ **数据库已初始化**：/home/wstpt/01_AI/02_Agent/07_pixie/02_code/data/data/agent.db
✅ **配置文件已就绪**：config/qa_agent_config.yaml
✅ **所有代码文件已创建**：完整的MVP系统

**⚠️ 缺少Flask依赖** - 需要先安装依赖包

## 测试步骤

1. 安装依赖（选择方案1或方案2）
2. 启动服务
3. 访问 http://localhost:5000
4. 在对话界面输入："你好"
5. 查看AI响应

## 配置API Key

编辑 `config/qa_agent_config.yaml`，填写您的API Key：

```yaml
# OpenAI（取消注释并填写）
llm:
  provider: "openai"
  api_key: "sk-proj-xxxxxxxxxxxxxxxxxxxx"

# 或通义千问（取消注释并填写）
llm:
  provider: "qwen"
  api_key: "sk-xxxxxxxxxxxxxxxxxxxx"
```

## 功能验证清单

启动后请验证以下功能：

- [ ] 访问Web界面正常
- [ ] 发送消息成功
- [ ] AI回复显示正常
- [ ] 对话历史保存
- [ ] Agent状态显示
- [ ] 任务历史查看
- [ ] 统计数据展示
- [ ] 清空对话功能
- [ ] 错误处理正常

## 常见问题

**Q1: 提示"ModuleNotFoundError: No module named 'flask'"**

A: 按照方案1或方案2安装Flask依赖

**Q2: 配置文件提示"API Key不能为空"**

A: 编辑 `config/qa_agent_config.yaml`，填写有效的API Key

**Q3: 无法访问localhost:5000**

A: 检查防火墙设置，确保端口5000未被阻止

**Q4: 数据库初始化失败**

A: 删除 `data/data/agent.db`，重新运行 `python3 data/init_db.py`

## 下一步

如果基础功能测试通过，可以考虑：

1. 添加更多Agent类型（数据分析、代码生成等）
2. 实现多Agent协同
3. 添加文件上传功能
4. 实现任务拆解与智能调度
5. 添加向量数据库，支持RAG
6. 实现WebSocket实时通信

---

**系统已就绪，等待您配置API Key后启动！** 🚀

