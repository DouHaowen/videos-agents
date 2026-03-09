# 快速启动指南

## 方式 1：使用启动脚本（推荐）

```bash
./start_web.sh
```

这个脚本会自动：
1. 创建虚拟环境（如果不存在）
2. 安装必要的依赖
3. 检查 .env 配置
4. 启动 Web 服务器

## 方式 2：手动启动

### 首次使用

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env 文件，填入 GOOGLE_API_KEY

# 5. 启动服务
python run_web.py
```

### 后续使用

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务
python run_web.py
```

## 访问地址

启动成功后，在浏览器打开：
- 本地访问: http://localhost:5000
- 局域网访问: http://你的IP:5000

## 常见问题

### 1. 端口被占用
如果 5000 端口被占用，编辑 `run_web.py`，修改端口号：
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # 改为 8080
```

### 2. 找不到模块
确保已激活虚拟环境：
```bash
source venv/bin/activate
```

### 3. API Key 未配置
确保 `.env` 文件存在且包含有效的 `GOOGLE_API_KEY`

### 4. 视频上传失败
- 检查文件大小（< 500MB）
- 检查磁盘空间
- 检查文件格式（MP4, MOV, AVI 等）

## 停止服务

在终端按 `Ctrl+C` 停止服务器

## 退出虚拟环境

```bash
deactivate
```
