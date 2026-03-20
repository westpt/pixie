# 数据持久化层验证手册

本文档提供了验证数据持久化层功能的所有方法和步骤。

## 目录
1. [快速验证](#快速验证)
2. [详细验证步骤](#详细验证步骤)
3. [手动验证方法](#手动验证方法)
4. [验证检查清单](#验证检查清单)

---

## 快速验证

### 自动化验证脚本（推荐）

运行自动化验证脚本可以一次性测试所有核心功能：

```bash
cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code
python verify_data_layer.py
```

**预期结果：**
- ✅ 所有6个验证部分都显示成功
- ✅ 生成的测试数据库：`data/test_verify.db`
- ✅ 生成的备份文件：`data/backup/full_backup_*.json`

### 单元测试验证

运行完整的单元测试套件：

```bash
cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code
python -m pytest tests/test_data_layer.py -v
```

**预期结果：**
- ✅ 33个测试全部通过
- ✅ 显示测试进度和结果
- ✅ 无测试失败或错误

---

## 详细验证步骤

### 第1步：验证数据库初始化

**目标**: 确认数据库表结构正确创建

```bash
# 初始化数据库
python data/init_db.py

# 验证表结构
python data/init_db.py --verify
```

**验证点：**
- [ ] 显示"数据库初始化成功"
- [ ] 数据库文件位置：`data/data/agent.db`
- [ ] 已创建的表：agents, tasks, results, config_history, roles, agent_roles
- [ ] 验证命令返回"数据库验证成功"

### 第2步：验证AgentsDAL功能

**目标**: 确认Agent数据的CRUD操作正常

创建测试脚本 `test_agents.py`：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data.agents_dal import AgentsDAL

# 初始化DAL
agents_dal = AgentsDAL()

# 1. 创建Agent
print("1. 创建Agent...")
config = {"api_key": "test_key", "model": "gpt-4"}
agent_id = agents_dal.create_agent("测试Agent", "qa", config)
print(f"   Agent ID: {agent_id}")

# 2. 查询Agent
print("2. 查询Agent...")
agent = agents_dal.get_agent_by_id(agent_id)
print(f"   Agent名称: {agent['name']}")
print(f"   Agent配置: {agent['config']}")

# 3. 更新状态
print("3. 更新状态...")
agents_dal.update_agent_status(agent_id, "running")
agent = agents_dal.get_agent_by_id(agent_id)
print(f"   新状态: {agent['status']}")

# 4. 更新配置
print("4. 更新配置...")
new_config = {"api_key": "new_key", "model": "gpt-4-turbo"}
agents_dal.update_agent_config(agent_id, new_config)
agent = agents_dal.get_agent_by_id(agent_id)
print(f"   新配置: {agent['config']}")

# 5. 获取所有Agent
print("5. 获取所有Agent...")
all_agents = agents_dal.get_all_agents()
print(f"   Agent总数: {len(all_agents)}")

# 6. 删除Agent
print("6. 删除Agent...")
agents_dal.delete_agent(agent_id)
print("   删除成功")
```

运行测试：
```bash
python test_agents.py
```

**验证点：**
- [ ] 创建Agent返回有效的ID
- [ ] 查询Agent返回正确的信息
- [ ] 配置JSON正确解析
- [ ] 状态更新成功
- [ ] 配置更新成功
- [ ] 获取列表包含创建的Agent
- [ ] 删除操作成功，再次查询返回None

### 第3步：验证TasksDAL功能

**目标**: 确认任务数据的CRUD操作正常

创建测试脚本 `test_tasks.py`：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data.tasks_dal import TasksDAL
from data.agents_dal import AgentsDAL

# 初始化DAL
tasks_dal = TasksDAL()
agents_dal = AgentsDAL()

# 先创建一个Agent（外键约束）
agent_id = agents_dal.create_agent("测试Agent", "qa", {"api_key": "test"})

# 1. 创建任务
print("1. 创建任务...")
internal_id = tasks_dal.create_task(
    task_id="test_task_001",
    content="测试问题",
    task_type="sync",
    priority="high"
)
print(f"   内部ID: {internal_id}")

# 2. 查询任务
print("2. 查询任务...")
task = tasks_dal.get_task_by_id("test_task_001")
print(f"   任务内容: {task['content']}")
print(f"   任务状态: {task['status']}")
print(f"   任务优先级: {task['priority']}")

# 3. 更新任务状态
print("3. 更新任务状态...")
tasks_dal.update_task_status("test_task_001", "processing", agent_id)
task = tasks_dal.get_task_by_id("test_task_001")
print(f"   新状态: {task['status']}")
print(f"   Agent ID: {task['agent_id']}")

# 4. 创建多个任务测试优先级排序
print("4. 创建多个任务...")
tasks_dal.create_task("task_002", "任务2", priority="low")
tasks_dal.create_task("task_003", "任务3", priority="medium")
tasks_dal.create_task("task_004", "任务4", priority="high")

# 5. 获取待处理任务（测试优先级排序）
print("5. 获取待处理任务（按优先级）...")
pending_tasks = tasks_dal.get_pending_tasks()
print(f"   待处理任务数: {len(pending_tasks)}")
for i, t in enumerate(pending_tasks, 1):
    print(f"   {i}. [{t['priority']}] {t['content']}")

# 6. 获取任务统计
print("6. 任务统计...")
count = tasks_dal.get_tasks_count()
print(f"   任务总数: {count}")
count_processing = tasks_dal.get_tasks_count(status="processing")
print(f"   处理中任务: {count_processing}")

# 7. 删除任务
print("7. 删除任务...")
tasks_dal.delete_task("test_task_001")
print("   删除成功")
```

运行测试：
```bash
python test_tasks.py
```

**验证点：**
- [ ] 创建任务返回有效的内部ID
- [ ] 查询任务返回正确的信息
- [ ] 状态更新成功，并记录开始时间
- [ ] 待处理任务按优先级排序（high > medium > low）
- [ ] 任务统计数字正确
- [ ] 删除操作成功

### 第4步：验证ResultsDAL功能

**目标**: 确认结果数据的CRUD和统计功能正常

创建测试脚本 `test_results.py`：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data.results_dal import ResultsDAL
from data.tasks_dal import TasksDAL
from data.agents_dal import AgentsDAL

# 初始化DAL
results_dal = ResultsDAL()
tasks_dal = TasksDAL()
agents_dal = AgentsDAL()

# 创建必要的关联数据
agent_id = agents_dal.create_agent("测试Agent", "qa", {"api_key": "test"})
tasks_dal.create_task("task_001", "问题1")
tasks_dal.create_task("task_002", "问题2")
tasks_dal.create_task("task_003", "问题3")

# 1. 创建结果
print("1. 创建结果...")
result_id = results_dal.create_result(
    task_id="task_001",
    content="测试回答",
    format="text",
    execution_time=1.5,
    status="success"
)
print(f"   结果ID: {result_id}")

# 2. 查询结果
print("2. 查询结果...")
result = results_dal.get_result_by_task_id("task_001")
print(f"   结果内容: {result['content']}")
print(f"   执行时间: {result['execution_time']}秒")
print(f"   结果状态: {result['status']}")

# 3. 创建多个结果（不同状态）
print("3. 创建多个结果...")
results_dal.create_result("task_002", "回答2", execution_time=2.0, status="success")
results_dal.create_result("task_003", "回答3", execution_time=3.0, status="failed")

# 4. 计算成功率
print("4. 计算成功率...")
success_rate = results_dal.get_success_rate()
print(f"   成功率: {success_rate*100:.1f}%")

# 5. 计算平均执行时间
print("5. 计算平均执行时间...")
avg_time = results_dal.get_average_execution_time(status="success")
print(f"   平均执行时间: {avg_time:.2f}秒")

# 6. 获取所有结果
print("6. 获取所有结果...")
all_results = results_dal.get_all_results()
print(f"   结果总数: {len(all_results)}")

# 7. 删除结果
print("7. 删除结果...")
results_dal.delete_result_by_task_id("task_001")
print("   删除成功")
```

运行测试：
```bash
python test_results.py
```

**验证点：**
- [ ] 创建结果返回有效的ID
- [ ] 查询结果返回正确的信息
- [ ] 执行时间正确记录
- [ ] 成功率计算正确（2/3 = 66.7%）
- [ ] 平均执行时间计算正确（(1.5+2.0)/2 = 1.75秒）
- [ ] 获取列表包含所有结果
- [ ] 删除操作成功

### 第5步：验证备份和恢复功能

**目标**: 确认数据库备份和恢复功能正常

#### 5.1 创建备份

```bash
# 完整备份（压缩格式）
python data/backup_db.py --full

# JSON格式备份
python data/backup_db.py --json

# 单表备份（CSV格式）
python data/backup_db.py --table agents

# 列出所有备份
python data/backup_db.py --list
```

**验证点：**
- [ ] 备份成功消息
- [ ] 备份文件生成在 `data/backup/` 目录
- [ ] 备份大小合理
- [ ] list命令显示所有备份文件
- [ ] 备份文件名包含时间戳

#### 5.2 验证备份

```bash
# 获取最新的备份文件名
ls -lt data/backup/full_backup_*.json | head -1

# 验证备份文件（替换为实际文件名）
python data/restore_db.py --verify data/backup/full_backup_20260318_210105.json
```

**验证点：**
- [ ] 验证成功消息
- [ ] 无错误或警告

#### 5.3 清理旧备份

```bash
# 清理7天前的备份
python data/backup_db.py --cleanup 7
```

**验证点：**
- [ ] 显示删除的旧备份文件
- [ ] 保留最新的备份文件

---

## 手动验证方法

### 方法1：使用SQLite命令行

直接操作测试数据库验证数据：

```bash
# 打开数据库
sqlite3 data/test_verify.db

# 查看所有表
.tables

# 查看agents表结构
.schema agents

# 查询所有Agent
SELECT * FROM agents;

# 查询所有任务（包括状态）
SELECT task_id, content, status, priority FROM tasks ORDER BY priority;

# 查询所有结果
SELECT task_id, execution_time, status FROM results;

# 统计查询
SELECT status, COUNT(*) FROM tasks GROUP BY status;

# 退出
.quit
```

### 方法2：使用Python交互

```bash
python
```

```python
from data.agents_dal import AgentsDAL
from data.tasks_dal import TasksDAL
from data.results_dal import ResultsDAL

# 初始化DAL
agents_dal = AgentsDAL()
tasks_dal = TasksDAL()
results_dal = ResultsDAL()

# 手动测试CRUD
agent_id = agents_dal.create_agent("手动测试", "qa", {"key": "value"})
print(f"Agent ID: {agent_id}")

agent = agents_dal.get_agent_by_id(agent_id)
print(f"Agent: {agent}")

task_id = tasks_dal.create_task("manual_task", "手动任务")
print(f"Task ID: {task_id}")

results = results_dal.get_all_results()
print(f"Results: {len(results)}")

# 退出
exit()
```

### 方法3：检查数据库文件

```bash
# 查看数据库文件大小
ls -lh data/data/agent.db

# 查看数据库表信息
sqlite3 data/data/agent.db ".schema"

# 查看数据库统计
sqlite3 data/data/agent.db <<EOF
SELECT 'agents' as table_name, COUNT(*) as count FROM agents
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks
UNION ALL
SELECT 'results', COUNT(*) FROM results;
EOF

# 查看索引信息
sqlite3 data/data/agent.db ".indexes"
```

---

## 验证检查清单

### 功能验证

**基础功能：**
- [ ] 数据库初始化成功
- [ ] 所有表创建正确
- [ ] 外键约束工作正常
- [ ] 索引创建正确

**AgentsDAL：**
- [ ] 创建Agent
- [ ] 查询Agent（按ID）
- [ ] 查询Agent（按名称）
- [ ] 更新Agent状态
- [ ] 更新Agent配置
- [ ] 获取所有Agent
- [ ] 按状态筛选Agent
- [ ] 获取Agent数量
- [ ] 删除Agent

**TasksDAL：**
- [ ] 创建任务
- [ ] 查询任务（按ID）
- [ ] 更新任务状态
- [ ] 更新任务分配
- [ ] 获取所有任务
- [ ] 按状态筛选任务
- [ ] 按优先级排序
- [ ] 按日期范围查询
- [ ] 获取任务数量
- [ ] 删除任务

**ResultsDAL：**
- [ ] 创建结果
- [ ] 查询结果（按任务ID）
- [ ] 获取所有结果
- [ ] 计算成功率
- [ ] 计算平均执行时间
- [ ] 获取结果数量
- [ ] 删除结果

**备份和恢复：**
- [ ] 完整数据库备份
- [ ] JSON格式备份
- [ ] CSV格式备份
- [ ] 列出备份文件
- [ ] 验证备份文件
- [ ] 恢复数据库
- [ ] 清理旧备份

### 测试验证

**单元测试：**
- [ ] 所有33个测试通过
- [ ] 无测试失败
- [ ] 无测试错误
- [ ] 测试覆盖率100%

**自动化验证脚本：**
- [ ] AgentsDAL验证通过
- [ ] TasksDAL验证通过
- [ ] ResultsDAL验证通过
- [ ] 集成测试通过
- [ ] 备份恢复验证通过

### 数据完整性验证

**外键约束：**
- [ ] tasks表的agent_id约束工作
- [ ] results表的task_id约束工作
- [ ] 级联删除正常

**数据一致性：**
- [ ] Agent状态转换合法
- [ ] 任务状态转换合法
- [ ] 时间戳正确记录
- [ ] JSON配置正确解析

### 性能验证

**查询性能：**
- [ ] 单表查询 < 10ms
- [ ] 多表关联查询 < 50ms
- [ ] 统计查询 < 100ms

**备份性能：**
- [ ] 完整备份 < 1秒（小数据量）
- [ ] JSON备份 < 2秒
- [ ] CSV备份 < 1秒

### 代码质量验证

**代码检查：**
- [ ] 无linter错误
- [ ] 无语法错误
- [ ] 符合PEP8规范
- [ ] 类型提示完整

**文档验证：**
- [ ] README已更新
- [ ] 验证手册已创建
- [ ] 使用示例完整
- [ ] 常见问题已更新

---

## 验证报告模板

完成验证后，填写以下报告：

```markdown
# 数据持久化层验证报告

**验证日期**: YYYY-MM-DD
**验证人**: [姓名]
**项目版本**: [版本号]

## 验证结果概览

- ✅ 功能验证: 通过/失败
- ✅ 单元测试: 33/33 通过
- ✅ 自动化验证: 通过/失败
- ✅ 数据完整性: 通过/失败
- ✅ 性能测试: 通过/失败

## 详细验证结果

### 功能验证
| 模块 | 功能 | 状态 | 备注 |
|------|------|------|------|
| AgentsDAL | 创建Agent | ✅ | |
| AgentsDAL | 查询Agent | ✅ | |
| ... | ... | ... | |

### 测试结果
| 测试套件 | 测试数 | 通过数 | 失败数 |
|----------|--------|--------|--------|
| test_data_layer.py | 33 | 33 | 0 |

### 性能指标
| 操作 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 单表查询 | <10ms | 5ms | ✅ |
| JSON备份 | <2s | 1.5s | ✅ |

## 发现的问题

| 问题ID | 严重程度 | 描述 | 状态 |
|--------|----------|------|------|
| 1 | 低 | ... | 已解决/待处理 |

## 总结与建议

[填写总结和建议]
```

---

## 常见问题排查

### Q: 数据库初始化失败

**可能原因：**
1. 数据库文件权限问题
2. 数据库文件被锁定
3. 磁盘空间不足

**解决方法：**
```bash
# 检查权限
ls -la data/data/

# 删除旧数据库
rm -f data/data/agent.db

# 重新初始化
python data/init_db.py --reset
```

### Q: 外键约束错误

**可能原因：**
1. 插入数据时引用的外键不存在
2. 删除顺序错误

**解决方法：**
```bash
# 先删除子表数据
DELETE FROM results WHERE task_id = 'xxx';
DELETE FROM tasks WHERE task_id = 'xxx';

# 再删除父表数据
DELETE FROM agents WHERE id = 1;
```

### Q: 备份文件无法打开

**可能原因：**
1. 备份文件损坏
2. 备份文件权限问题

**解决方法：**
```bash
# 检查文件完整性
python data/restore_db.py --verify data/backup/xxx.json

# 检查文件权限
ls -la data/backup/

# 重新备份
python data/backup_db.py --json
```

### Q: 测试失败

**可能原因：**
1. 依赖包版本不匹配
2. Python版本不兼容
3. 数据库未初始化

**解决方法：**
```bash
# 重新安装依赖
pip install -r requirements.txt

# 初始化测试数据库
python data/init_db.py --reset

# 重新运行测试
python -m pytest tests/test_data_layer.py -v
```

---

## 联系与支持

如遇到验证问题，请：
1. 查看本文档的常见问题部分
2. 查看项目README.md
3. 提交Issue或联系开发团队

---

**文档版本**: 1.0
**最后更新**: 2026-03-18
