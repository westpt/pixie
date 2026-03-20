# 数据持久化层快速验证指南

## 🚀 快速开始（3步验证）

### 步骤1: 运行自动化验证脚本

```bash
cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code
python verify_data_layer.py
```

**期望看到**：
- ✅ 6个验证部分全部通过
- ✅ 测试数据库：`data/test_verify.db`
- ✅ 备份文件：`data/backup/full_backup_*.json`

### 步骤2: 运行单元测试

```bash
python -m pytest tests/test_data_layer.py -v
```

**期望看到**：
- ✅ 33个测试全部通过
- ✅ 测试进度：33 passed in ~5s

### 步骤3: 手动查看数据库

```bash
sqlite3 data/test_verify.db

# 查看表
.tables

# 查看数据
SELECT * FROM agents;
SELECT * FROM tasks;
SELECT * FROM results;

# 退出
.quit
```

**期望看到**：
- ✅ agents表有数据
- ✅ tasks表有数据
- ✅ results表有数据

---

## 📋 验证命令速查表

| 验证目标 | 命令 | 预期结果 |
|---------|------|----------|
| 自动化验证 | `python verify_data_layer.py` | ✅ 所有验证通过 |
| 单元测试 | `pytest tests/test_data_layer.py -v` | ✅ 33 passed |
| 数据库初始化 | `python data/init_db.py` | ✅ 数据库创建成功 |
| 数据库验证 | `python data/init_db.py --verify` | ✅ 数据库验证成功 |
| 完整备份 | `python data/backup_db.py --full` | ✅ 备份成功 |
| JSON备份 | `python data/backup_db.py --json` | ✅ 备份成功 |
| 列出备份 | `python data/backup_db.py --list` | ✅ 显示备份列表 |
| 验证备份 | `python data/restore_db.py --verify <backup>` | ✅ 验证成功 |

---

## 🎯 核心验证命令

### 1. 数据库相关

```bash
# 初始化数据库
python data/init_db.py

# 重置数据库
python data/init_db.py --reset

# 验证数据库
python data/init_db.py --verify
```

### 2. 备份相关

```bash
# 完整备份（压缩）
python data/backup_db.py --full

# 完整备份（不压缩）
python data/backup_db.py --full --no-compress

# JSON格式备份
python data/backup_db.py --json

# 单表备份（CSV）
python data/backup_db.py --table agents
python data/backup_db.py --table tasks
python data/backup_db.py --table results

# 列出所有备份
python data/backup_db.py --list

# 清理旧备份（保留7天）
python data/backup_db.py --cleanup 7
```

### 3. 恢复相关

```bash
# 验证备份文件
python data/restore_db.py --verify data/backup/full_backup_*.json

# 恢复数据库（谨慎使用）
python data/restore_db.py data/backup/full_backup_*.db

# 恢复单个表
python data/restore_db.py --table data/backup/agents_*.csv agents
```

### 4. 测试相关

```bash
# 运行所有测试
pytest tests/ -v

# 运行数据持久化层测试
pytest tests/test_data_layer.py -v

# 运行特定测试
pytest tests/test_data_layer.py::TestBaseDAL -v

# 查看测试覆盖率
pytest tests/ --cov=data --cov-report=html
```

---

## 📊 验证数据检查点

### 数据库表结构检查

```bash
sqlite3 data/test_verify.db <<EOF
-- 检查表是否存在
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- 检查agents表结构
PRAGMA table_info(agents);

-- 检查tasks表结构
PRAGMA table_info(tasks);

-- 检查results表结构
PRAGMA table_info(results);

-- 检查索引
PRAGMA index_list(agents);
PRAGMA index_list(tasks);
PRAGMA index_list(results);
EOF
```

**期望输出**：
- agents表字段：id, name, type, config, status, created_at, updated_at
- tasks表字段：id, task_id, content, task_type, priority, status, agent_id, created_at, started_at, completed_at
- results表字段：id, task_id, content, format, execution_time, status, created_at
- 索引：每个表都有相应的索引

### 数据完整性检查

```bash
sqlite3 data/test_verify.db <<EOF
-- 检查外键约束
SELECT * FROM pragma_foreign_key_check();

-- 检查数据统计
SELECT 'agents' as table_name, COUNT(*) as count FROM agents
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks
UNION ALL
SELECT 'results', COUNT(*) FROM results;

-- 检查Agent状态分布
SELECT status, COUNT(*) FROM agents GROUP BY status;

-- 检查任务状态分布
SELECT status, COUNT(*) FROM tasks GROUP BY status;

-- 检查结果状态分布
SELECT status, COUNT(*) FROM results GROUP BY status;
EOF
```

**期望输出**：
- 外键检查：无错误
- 数据统计：每个表都有数据
- 状态分布：合法的状态值

---

## 🐛 问题诊断

### 问题1: 数据库初始化失败

**症状**：
```
Error: 数据库初始化失败 - database is locked
```

**解决方法**：
```bash
# 检查是否有进程占用数据库
lsof data/data/agent.db

# 删除锁文件
rm -f data/data/agent.db-lock

# 重新初始化
python data/init_db.py --reset
```

### 问题2: 备份失败

**症状**：
```
Error: 备份失败 - Permission denied
```

**解决方法**：
```bash
# 检查备份目录权限
ls -la data/backup/

# 创建备份目录（如果不存在）
mkdir -p data/backup/

# 设置正确权限
chmod 755 data/backup/

# 重新备份
python data/backup_db.py --json
```

### 问题3: 测试失败

**症状**：
```
FAILED tests/test_data_layer.py::TestAgentsDAL::test_create_agent
```

**解决方法**：
```bash
# 确保数据库已初始化
python data/init_db.py --reset

# 重新安装依赖
pip install -r requirements.txt

# 清理测试缓存
pytest tests/ --cache-clear

# 重新运行测试
pytest tests/test_data_layer.py -v
```

### 问题4: 外键约束错误

**症状**：
```
DatabaseError: 数据完整性错误：FOREIGN KEY constraint failed
```

**解决方法**：
```bash
# 检查外键关系
sqlite3 data/test_verify.db <<EOF
-- 检查tasks表的外键
PRAGMA foreign_key_list(tasks);

-- 检查results表的外键
PRAGMA foreign_key_list(results);
EOF

# 确保引用的数据存在
# 1. 先创建Agent
# 2. 再创建Task（引用Agent）
# 3. 最后创建Result（引用Task）
```

---

## ✅ 验证成功标志

如果看到以下所有标志，说明验证成功：

### 自动化验证脚本
- ✅ 初始化测试数据库成功
- ✅ AgentsDAL功能测试通过
- ✅ TasksDAL功能测试通过
- ✅ ResultsDAL功能测试通过
- ✅ 完整工作流测试通过
- ✅ 备份和恢复测试通过

### 单元测试
- ✅ 33个测试全部通过
- ✅ 0个测试失败
- ✅ 0个测试错误
- ✅ 执行时间约5秒

### 数据库
- ✅ 所有表创建正确
- ✅ 所有索引创建正确
- ✅ 外键约束工作正常
- ✅ 数据可以正常查询

### 备份恢复
- ✅ 备份文件生成成功
- ✅ 备份文件可以验证
- ✅ 备份文件可以恢复
- ✅ 旧备份可以清理

---

## 📞 获取帮助

如果遇到验证问题：

1. **查看详细验证手册**
   ```bash
   cat VERIFICATION.md
   ```

2. **查看项目README**
   ```bash
   cat README.md
   ```

3. **查看测试代码**
   ```bash
   cat tests/test_data_layer.py
   ```

4. **查看验证脚本**
   ```bash
   cat verify_data_layer.py
   ```

5. **查看日志**
   ```bash
   tail -f logs/agent.log
   ```

---

## 📝 验证记录模板

完成验证后，记录以下信息：

```text
数据持久化层验证记录
====================

验证日期: ________________
验证人: ________________
项目版本: ______________

验证结果:
- 自动化验证: [ ] 通过 / [ ] 失败
- 单元测试: [ ] 通过 / [ ] 失败
- 测试通过数: __/33
- 数据完整性: [ ] 通过 / [ ] 失败
- 备份恢复: [ ] 通过 / [ ] 失败

发现的问题:
1. ________________
2. ________________
3. ________________

备注:
______________
```

---

## 🔄 重新验证流程

如果修改了代码，需要重新验证：

```bash
# 1. 清理旧测试数据
rm -f data/test_verify.db
rm -f data/backup/full_backup_*.json

# 2. 运行验证脚本
python verify_data_layer.py

# 3. 运行单元测试
pytest tests/test_data_layer.py -v

# 4. 检查linter错误
# （在IDE中查看或运行linter命令）

# 5. 确认所有检查通过
```

---

**快速验证指南版本**: 1.0
**最后更新**: 2026-03-18
**相关文档**: README.md, VERIFICATION.md
