# AI Agent Framework - 测试指南

## 🎯 测试目标

验证AI Agent Framework MVP的核心功能是否正常工作。

---

## 📋 前置条件检查

### 1. 检查文件完整性

```bash
cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code

# 检查关键文件是否存在
ls -l data/agent.db
ls -l config/qa_agent_config.yaml
ls -l app.py
ls -l web/templates/index.html
```

预期结果：
- ✅ `data/data/agent.db` 存在
- ✅ `config/qa_agent_config.yaml` 存在
- ✅ `app.py` 存在
- ✅ `web/templates/index.html` 存在

### 2. 检查数据库初始化

```bash
# 初始化数据库（如果未初始化）
python3 data/init_db.py
```

预期输出：
```
创建agents表...
创建tasks表...
创建results表...
创建config_history表...

数据库初始化成功！
数据库位置：/home/wstpt/01_AI/02_Agent/07_pixie/02_code/data/data/agent.db
```

### 3. 检查Python依赖

```bash
# 检查Flask是否安装
python3 -c "import flask; print('✓ Flask已安装')" 2>&1 || echo "✗ Flask未安装"

# 检查PyYAML是否安装
python3 -c "import yaml; print('✓ PyYAML已安装')" 2>&1 || echo "✗ PyYAML未安装"

# 检查requests是否安装
python3 -c "import requests; print('✓ requests已安装')" 2>&1 || echo "✗ requests未安装"
```

预期结果：
- ✅ Flask已安装
- ✅ PyYAML已安装
- ✅ requests已安装

**如果任一未安装**，请运行：
```bash
# 使用Jarvis虚拟环境安装
/home/wstpt/01_AI/02_Agent/07_pixie/02_Jarvis/.venv/bin/pip install -r requirements.txt
```

---

## 🚀 启动服务

### 方法1：使用Jarvis Python环境（推荐）

```bash
cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code

# 启动Flask服务
/home/wstpt/01_AI/02_Agent/07_pixie/02_Jarvis/.venv/bin/python app.py
```

### 方法2：后台启动

```bash
cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code

# 后台启动
/home/wstpt/01_AI/02_Agent/07_pixie/02_Jarvis/.venv/bin/python app.py > /tmp/app.log 2>&1 &

# 查看进程ID
echo $!
```

### 方法3：使用nohup（持久化运行）

```bash
cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code

# 使用nohup启动（断开SSH后继续运行）
nohup /home/wstpt/01_AI/02_Agent/07_pixie/02_Jarvis/.venv/bin/python app.py > /tmp/app.log 2>&1 &

# 查看日志
tail -f /tmp/app.log
```

---

## 🧪 功能测试

### 测试1：访问Web界面

**步骤**：
1. 等待3-5秒，让服务完全启动
2. 打开浏览器，访问：http://localhost:5000
3. 检查页面是否正常显示

**预期结果**：
- ✅ 页面标题显示"AI Agent Framework"
- ✅ 显示4个标签：💬 对话、📋 任务历史、🤖 Agent状态、📊 统计
- ✅ 显示欢迎消息："欢迎使用AI Agent Framework！"
- ✅ 输入框可以输入文字
- ✅ "发送"和"清空对话"按钮可点击

**失败原因**：
- 🔴 页面无法访问 → 检查防火墙，确保端口5000未阻止
- 🔴 页面样式异常 → 检查CSS文件是否正确加载
- 🔴 页面空白 → 查看浏览器控制台错误信息

---

### 测试2：健康检查API

**步骤**：
```bash
# 检查服务健康状态
curl http://localhost:5000/api/health
```

**预期输出**：
```json
{
  "status": "healthy",
  "timestamp": "2026-03-03T...",
  "agent": {
    "name": null,
    "status": "not_loaded"
  }
}
```

**失败原因**：
- 🔴 返回错误 → 检查Flask是否正常启动
- 🔴 连接被拒绝 → 检查端口是否被占用

---

### 测试3：发送消息

**步骤**：
1. 在Web界面的"对话"标签，输入框中输入："你好"
2. 点击"发送"按钮
3. 观察AI回复

**预期结果**：
- ✅ 显示"处理中..."加载动画
- ✅ 3-10秒后显示AI回复
- ✅ 对话框中出现用户消息（白色背景，右侧）
- ✅ 对话框中出现AI回复（蓝色背景，左侧）

**失败原因**：
- 🔴 长时间无响应 → 检查API Key是否有效，检查网络连接
- 🔴 显示错误消息 → 查看浏览器控制台或日志文件

---

### 测试4：对话历史

**步骤**：
1. 切换到"任务历史"标签
2. 查看是否显示刚才发送的任务

**预期结果**：
- ✅ 任务列表显示刚才发送的"你好"任务
- ✅ 任务状态为"已完成"
- ✅ 任务内容显示"你好"
- ✅ 可以看到结果内容（AI回复）

**失败原因**：
- 🔴 任务列表为空 → 检查数据库是否有数据
- 🔴 无法加载任务 → 检查API接口是否正常

---

### 测试5：Agent状态

**步骤**：
1. 切换到"Agent状态"标签
2. 查看Agent信息

**预期结果**（配置API Key后）：
- ✅ Agent名称："QA助手"
- ✅ Agent类型："qa_assistant"
- ✅ Agent状态："运行中"
- ✅ Agent ID显示
- ✅ 已处理任务数：1或更多
- ✅ 错误次数：0或实际数值

**预期结果**（未配置API Key）：
- ✅ Agent状态："not_loaded"
- ✅ 提示"Agent未加载"

---

### 测试6：统计面板

**步骤**：
1. 切换到"统计"标签
2. 查看统计数据

**预期结果**：
- ✅ 显示4个统计卡片
- ✅ 总任务数：实际数值
- ✅ 待处理数：实际数值
- ✅ 成功率：百分比（如0.0%）
- ✅ 平均响应时间：秒数（如0.00秒）

**失败原因**：
- 🔴 统计数据为空 → 发送几条消息后再测试
- 🔴 数据显示异常 → 检查数据库查询接口

---

### 测试7：清空对话

**步骤**：
1. 在"对话"标签，发送多条消息
2. 点击"清空对话"按钮
3. 观察对话列表

**预期结果**：
- ✅ 对话列表清空，只显示系统欢迎消息
- ✅ 显示成功提示："对话历史已清空"

**失败原因**：
- 🔴 对话未清空 → 检查清空接口是否正常
- 🔴 提示未显示 → 检查JavaScript事件是否绑定

---

### 测试8：上下文记忆

**步骤**：
1. 在"对话"标签，发送："什么是人工智能？"
2. 等待AI回复
3. 继续发送："它有哪些应用？"
4. 观察AI是否理解上下文

**预期结果**：
- ✅ AI在回答第二个问题时，引用第一个问题的内容
- ✅ 对话连续流畅，没有割裂感

**失败原因**：
- 🔴 AI不理解上下文 → 检查对话历史是否正确保存
- 🔴 回答不连贯 → 检查历史记录大小限制

---

### 测试9：错误处理

**步骤**：
1. 在配置文件中填写错误的API Key（如："invalid-key"）
2. 重启服务
3. 发送消息："你好"

**预期结果**：
- ✅ 不显示错误消息，而是显示系统提示
- ✅ 控制台记录错误日志
- ✅ 日志文件记录错误详情

**失败原因**：
- 🔴 页面崩溃 → 检查错误处理逻辑
- 🔴 日志未记录 → 检查日志配置

---

## 📊 性能测试

### 测试10：响应时间

**步骤**：
1. 发送10条简单的测试消息
2. 记录每条消息的响应时间
3. 计算平均响应时间

**预期结果**：
- ✅ 平均响应时间 < 5秒（OpenAI API）
- ✅ 所有消息都在30秒内响应

**失败原因**：
- 🔴 响应时间 > 10秒 → 网络慢或API有问题
- 🔴 部分消息超时 → 检查超时配置

---

### 测试11：并发测试

**步骤**：
1. 打开两个浏览器标签
2. 同时发送不同的消息
3. 观察是否能正确处理

**预期结果**：
- ✅ 两个消息都能正常处理
- ✅ 不会出现请求冲突
- ✅ 数据正确写入数据库

**失败原因**：
- 🔴 一个消息处理失败 → 数据库并发问题
- 🔴 消息混乱 → 检查任务ID生成

---

## 📝 测试记录模板

```markdown
## 测试报告

**测试日期**：2026-03-03
**测试人员**：[填写姓名]
**系统版本**：MVP v1.0

### 测试结果汇总

| 测试项 | 结果 | 备注 |
|---------|------|------|
| 文件完整性检查 | ✅/❌ | |
| 数据库初始化 | ✅/❌ | |
| Web界面访问 | ✅/❌ | |
| 健康检查API | ✅/❌ | |
| 发送消息 | ✅/❌ | |
| 对话历史 | ✅/❌ | |
| Agent状态 | ✅/❌ | |
| 统计面板 | ✅/❌ | |
| 清空对话 | ✅/❌ | |
| 上下文记忆 | ✅/❌ | |
| 错误处理 | ✅/❌ | |
| 响应时间 | ✅/❌ | 平均：X秒 |
| 并发测试 | ✅/❌ | |

### 问题列表

1. [问题描述]
   - 重现步骤：
   - 错误信息：
   - 影响范围：
   - 建议解决方案：
   - 优先级：高/中/低

### 改进建议

1. [改进建议1]
2. [改进建议2]

### 结论

[测试结论]

---

## 🔍 调试技巧

### 查看日志

```bash
# 查看运行日志
tail -f /home/wstpt/01_AI/02_Agent/07_pixie/02_code/logs/qa_agent.log

# 查看Flask日志（如果启动时指定了日志文件）
tail -f /tmp/app.log
```

### 检查进程

```bash
# 查看Python进程
ps aux | grep python

# 查看端口占用
netstat -tulnp | grep :5000

# 杀掉占用5000端口的进程
kill -9 [PID]
```

### 检查数据库

```bash
# 进入数据库命令行
sqlite3 /home/wstpt/01_AI/02_Agent/07_pixie/02_code/data/data/agent.db

# 查看表结构
.schema agents
.schema tasks
.schema results

# 查询数据
SELECT * FROM tasks;
SELECT * FROM results;
SELECT * FROM agents;
```

---

## ✅ 测试完成标准

所有核心功能通过以下标准：

1. ✅ Web界面正常显示
2. ✅ 消息发送成功
3. ✅ AI响应正常
4. ✅ 对话历史保存
5. ✅ Agent状态更新
6. ✅ 统计数据准确
7. ✅ 错误处理正确
8. ✅ 响应时间合理（< 10秒）
9. ✅ 并发处理正常
10. ✅ 上下文记忆有效

**如果所有测试通过**，MVP开发完成！🎉

---

## 📞 获取帮助

遇到问题？

1. 查看README.md：完整的使用文档
2. 查看QUICKSTART.md：快速启动指南
3. 查看logs/qa_agent.log：运行日志
4. 检查Flask文档：https://flask.palletsprojects.com/
5. 查看Python文档：https://docs.python.org/3/

---

**祝测试顺利！** 🚀

