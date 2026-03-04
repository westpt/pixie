#!/bin/bash
# AI Agent Framework - 启动脚本

echo "======================================================"
echo "  AI Agent Framework - 启动脚本"
echo "======================================================"
echo ""

# 检查Python版本
echo "📋 检查Python版本..."
python3 --version
echo ""

# 初始化数据库
echo "🗄️  初始化数据库..."
python3 data/init_db.py
echo ""

# 检查配置文件
echo "⚙️  检查配置文件..."
if [ ! -f "config/qa_agent_config.yaml" ]; then
    echo "✗ 错误：配置文件不存在：config/qa_agent_config.yaml"
    echo ""
    echo "请先创建配置文件："
    echo "  cp config/templates/agent_template.yaml config/qa_agent_config.yaml"
    echo "  编辑 config/qa_agent_config.yaml，填写API Key"
    echo ""
    exit 1
else
    echo "✓ 配置文件存在"
fi
echo ""

# 创建日志目录
echo "📝 创建日志目录..."
mkdir -p logs
echo "✓ 日志目录就绪"
echo ""

# 检查依赖
echo "📦 检查依赖包..."
python3 -c "import flask, yaml, requests; print('✓ 所有依赖已安装')" 2>/dev/null || {
    echo "✗ 部分依赖缺失，正在安装..."
    pip3 install -r requirements.txt
}
echo ""

# 启动服务
echo "🚀 启动Web服务..."
echo ""
echo "服务地址：http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""
echo "======================================================"

# 启动Flask应用
python3 app.py

