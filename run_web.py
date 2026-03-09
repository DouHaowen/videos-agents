#!/usr/bin/env python3
"""
启动 Web 服务器
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*60)
    print("🌐 会议视频分析系统 Web 版")
    print("="*60)
    print("\n📍 本地访问: http://localhost:8080")
    print("📍 局域网访问: http://你的IP:8080")
    print("\n💡 提示: 首次使用请确保已配置 .env 文件中的 GOOGLE_API_KEY")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(debug=True, host='0.0.0.0', port=8080)
