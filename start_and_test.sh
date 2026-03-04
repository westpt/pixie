#!/bin/bash
# AI Agent Framework - 简化启动与测试脚本

echo "=================================================="
echo "  AI Agent Framework - 启动中..."
echo "=================================================="
echo ""

cd /home/wstpt/01_AI/02_Agent/07_pixie/02_code

# 激活虚拟环境
echo "1. 激活虚拟环境..."
source .venv/bin/activate

# 初始化数据库
echo "2. 初始化数据库..."
python data/init_db.py
if [ $? -ne 0 ]; then
    echo "   ✗ 数据库初始化失败"
    exit 1
fi
echo "   ✓ 数据库初始化成功"

# 启动Flask服务（前台，查看实时输出）
echo "3. 启动Flask服务（前台模式，Ctrl+C可停止）..."
echo ""
echo "服务地址：http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

python app.py

