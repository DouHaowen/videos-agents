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
    
    # 尝试多个端口
    ports = [8080, 8081, 8082, 5001, 5002, 9000]
    port = None
    
    for p in ports:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', p))
            sock.close()
            port = p
            break
        except OSError:
            continue
    
    if port is None:
        print("❌ 错误: 所有端口都被占用")
        print("   请手动停止其他服务或指定端口: PORT=9000 python run_web.py")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🌐 会议视频分析系统 Web 版")
    print("="*60)
    print(f"\n📍 本地访问: http://localhost:{port}")
    print(f"📍 局域网访问: http://你的IP:{port}")
    print("\n💡 提示: 首次使用请确保已配置 .env 文件中的 GOOGLE_API_KEY")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(debug=True, host='0.0.0.0', port=port)
