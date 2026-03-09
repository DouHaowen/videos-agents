# GitHub 提交指南

## ⚠️ 重要安全提示
你刚才分享的 GitHub Token 已经暴露，建议立即：
1. 访问 https://github.com/settings/tokens
2. 撤销刚才的 token
3. 生成一个新的 token

## 提交步骤

打开终端，执行以下命令：

```bash
# 进入项目目录
cd /Users/saita/saita/videos-agnets

# 初始化 git
git init

# 添加所有文件
git add -A

# 提交
git commit -m "Initial commit: Multi-model video analysis system"

# 设置主分支
git branch -M main

# 添加远程仓库
git remote add origin https://github.com/DouHaowen/videos-agents.git

# 推送（会提示输入用户名和密码）
git push -u origin main
```

## 认证方式

### 方式 1: 使用 Token（推荐）
当提示输入密码时：
- Username: DouHaowen
- Password: 粘贴你的新 token（不是密码）

### 方式 2: 使用 SSH
```bash
# 如果你已配置 SSH key
git remote set-url origin git@github.com:DouHaowen/videos-agents.git
git push -u origin main
```

### 方式 3: 在 URL 中包含 token
```bash
git remote set-url origin https://YOUR_NEW_TOKEN@github.com/DouHaowen/videos-agents.git
git push -u origin main
```

## 验证

推送成功后，访问：
https://github.com/DouHaowen/videos-agents

应该能看到所有代码文件。
