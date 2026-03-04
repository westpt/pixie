#!/bin/bash
# AI Agent Framework - 完整测试脚本

echo "=================================================="
echo "  AI Agent Framework - 完整测试与诊断"
echo "=================================================="
echo ""

cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code

# 检查1：Python环境
echo "1️⃣  检查Python环境..."
echo ""
python3 --version
echo ""
echo "2️⃣  检查项目文件..."
echo ""
ls -la | head -20
echo ""

# 检查2：依赖安装
echo "3️⃣  检查Python依赖..."
echo ""
source .venv/bin/activate
python3 -c "import flask, yaml, requests; print('✓')" 2>&1 || echo "✗"
echo ""

# 检查3：数据库状态
echo "4️⃣  检查数据库..."
echo ""
if [ -f data/data/agent.db ]; then
    echo "✅ 数据库文件存在"
    sqlite3 data/data/agent.db ".tables agents" | head -1
    DB_SIZE=$(stat -f%z data/data/agent.db | cut -f1 -d' ')
    echo "   数据库大小：${DB_SIZE} 字节"
else
    echo "✗ 数据库文件不存在"
fi
echo ""

# 检查4：配置文件
echo "5️⃣  检查配置文件..."
echo ""
if [ -f config/qa_agent_config.yaml ]; then
    echo "✅ 配置文件存在"
    python3 -c "import yaml; print('✓ 配置可解析')" 2>&1 || echo "✗"
else
    echo "✗ 配置文件不存在，请先创建"
fi
echo ""

# 测试选项
echo "6️⃣  测试选项："
echo ""
echo "请选择测试类型："
echo "  1) 完整环境检查"
echo "  2) 数据库诊断"
echo "  3) 重置数据库"
echo "  4) 清理数据库"
echo "  5) 测试Flask启动（前台）"
echo "  6) 测试API接口"
echo ""
read -p "请输入选项 (1-6): " choice

case $choice in
    1)
        echo ""
        echo "=================================================="
        echo "  🔍 完整环境检查"
        echo "=================================================="
        echo ""
        echo "1.1️⃣  检查Python版本..."
        python3 --version
        echo ""
        echo "1.2️⃣  检查项目文件..."
        ls -la
        echo ""
        echo "1.3️⃣  检查虚拟环境..."
        source .venv/bin/activate
        python3 --version
        echo ""
        echo "1.4️⃣  检查依赖安装..."
        pip list | grep -E "(flask|yaml|requests)"
        echo ""
        echo "按任意键继续..."
        read -n -s -r -p ""
        ;;
    
    2)
        echo ""
        echo "=================================================="
        echo "  🔍 数据库诊断"
        echo "=================================================="
        echo ""
        sqlite3 data/data/agent.db ".tables" | head -5
        sqlite3 data/data/agent.db "SELECT COUNT(*) as count FROM agents;"
        sqlite3 data/data/agent.db "SELECT COUNT(*) as count FROM tasks;"
        echo ""
        echo "按任意键继续..."
        read -n -s -r -p ""
        ;;
    
    3)
        echo ""
        echo "=================================================="
        echo "  🔄 重置数据库"
        echo "=================================================="
        echo ""
        echo "⚠️  警告：此操作将删除所有数据！"
        read -p "确认重置？: " choice
        case $REPLY in
            y|Y)
                rm -f data/data/agent.db
                python3 data/init_db.py
                echo "✅ 数据库已重置"
                ;;
            n|N)
                echo "已取消"
                ;;
        esac
        echo ""
        echo "按任意键继续..."
        read -n -s -r -p ""
        ;;
    
    4)
        echo ""
        echo "=================================================="
        echo "  🧹 清理数据库"
        echo "=================================================="
        echo ""
        echo "⚠️  警告：将清理30天前的历史数据"
        read -p "确认清理？: " choice
        case $REPLY in
            y|Y)
                python3 -c "from datetime import datetime; import sqlite3; conn = sqlite3.connect('data/data/agent.db'); cursor = conn.cursor(); thirty_days_ago = (datetime.now() - datetime.timedelta(days=30)).isoformat(); cursor.execute('DELETE FROM tasks WHERE created_at < ?', (thirty_days_ago,)); conn.commit(); print('已清理')"; conn.close()"
                ;;
            n|N)
                echo "已取消"
                ;;
        esac
        echo ""
        echo "按任意键继续..."
        read -n -s -r -p ""
        ;;
    
    5)
        echo ""
        echo "=================================================="
        echo "  🧪 测试Flask启动（前台）"
        echo "=================================================="
        echo ""
        echo "⚠️  注意：前台模式将显示所有输出，按Ctrl+C停止"
        echo ""
        echo "启动Flask服务..."
        source .venv/bin/activate
        python3 app.py
        ;;
    
    6)
        echo ""
        echo "=================================================="
        echo "  🌐 测试API接口"
        echo "=================================================="
        echo ""
        echo "测试1：健康检查..."
        curl -s http://localhost:5000/api/health 2>&1 | grep -E "(healthy|status)"
        echo ""
        echo "测试2：Agent状态查询..."
        curl -s http://localhost:5000/api/agents/status 2>&1 | grep -E "(agent_id|name|status)"
        echo ""
        echo "测试3：任务历史查询..."
        curl -s http://localhost:5000/api/tasks 2>&1 | grep -E "(task_id|content|status)"
        echo ""
        echo "按任意键继续..."
        read -n -s -r -p ""
        ;;
    
    *)
        echo ""
        echo "❌ 无效选项，请重新选择"
        echo ""
        exit 1
        ;;

echo ""
echo "=================================================="
echo "  测试完成，按Ctrl+C退出"
echo "=================================================="

