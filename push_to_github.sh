#!/bin/bash
# Git 提交脚本

echo "🚀 开始提交代码到 GitHub..."

# 初始化 git（如果还没有）
if [ ! -d .git ]; then
    git init
    echo "✓ Git 仓库初始化完成"
fi

# 添加所有文件
git add -A
echo "✓ 文件已添加"

# 提交
git commit -m "Initial commit: Multi-model video analysis system

Features:
- Support 4 AI models: Gemini, GPT-4o, Claude, Qwen2-VL
- Direct video analysis with native video support
- Multi-model comparison tool
- Beautiful HTML reports
- Automatic scene classification
"
echo "✓ 代码已提交"

# 设置主分支
git branch -M main
echo "✓ 主分支设置完成"

# 添加远程仓库
git remote add origin https://github.com/DouHaowen/videos-agents.git 2>/dev/null || git remote set-url origin https://github.com/DouHaowen/videos-agents.git
echo "✓ 远程仓库已配置"

# 推送到 GitHub
git push -u origin main
echo "✅ 代码已推送到 GitHub!"
