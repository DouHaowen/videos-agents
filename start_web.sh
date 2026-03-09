#!/bin/bash
# 启动脚本（使用虚拟环境）

echo "🚀 启动会议视频分析系统..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 检查依赖..."
pip install -q flask google-generativeai python-dotenv opencv-python moviepy 2>/dev/null

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到 .env 文件"
    echo "📝 请复制 .env.example 为 .env 并配置 API Key"
    echo ""
    read -p "是否现在创建 .env 文件? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✅ 已创建 .env 文件，请编辑并填入你的 GOOGLE_API_KEY"
        exit 0
    fi
fi

# 启动服务
echo ""
echo "🌐 启动 Web 服务器..."
python run_web.py
