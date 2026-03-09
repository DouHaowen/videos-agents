# 会议视频分析系统 🎬

AI 驱动的智能会议分析工具，支持 Web 界面、智能分段、发言人识别、决策点检测、多格式导出和知识库管理。

## ✨ 核心功能

### 🌐 Web 界面（推荐）
- ✅ **拖拽上传** - 简单易用的 Web 界面
- ✅ **实时进度** - 可视化分析进度
- ✅ **在线查看** - 直接在浏览器查看报告
- ✅ **一键下载** - 下载多种格式报告

### 🎯 完整分析功能
- ✅ **智能分段** - 自动识别议题切换点，生成时间轴
- ✅ **待办事项提取** - 识别任务、负责人、截止日期
- ✅ **发言人识别** - 识别不同发言人及参与度
- ✅ **决策点检测** - 自动标注关键决策时刻
- ✅ **多格式导出** - Markdown、HTML、PDF
- ✅ **知识库管理** - 存储和搜索历史会议

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 API Key
```bash
cp .env.example .env
# 编辑 .env，填入 GOOGLE_API_KEY
```

### 3. 启动 Web 服务（推荐）

```bash
# 使用虚拟环境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

python run_web.py
```

然后在浏览器打开：**http://localhost:8080**

## 📱 使用方式

### 方式 1：Web 界面（推荐）⭐

```bash
python run_web.py
```

**功能**：
- 📤 拖拽或点击上传视频
- 🔬 选择分析模式（深度/快速）
- 📊 实时查看分析进度
- 🎨 在线查看交互式报告
- 💾 一键下载多种格式

### 方式 2：命令行完整分析

```bash
python analyze_complete.py your_video.mp4
```

**输出内容**（11种文件）：
- `basic_analysis.json` - 基础分析
- `segments.json` - 智能分段
- `action_items.json` - 待办事项
- `speakers.json` - 发言人信息
- `decisions.json` - 决策点
- `meeting_minutes.md` - 会议纪要
- `speaker_report.md` - 发言人报告
- `decision_report.md` - 决策点报告
- `timeline_report.html` - 时间轴报告
- `meeting_report.pdf` - PDF 报告
- `statistics.json` - 统计信息

### 方式 3：快速分析

```bash
python analyze_meeting_deep.py your_video.mp4  # 深度分析（P0功能）
python analyze_with_gemini.py your_video.mp4   # 快速分析
```

### 方式 4：多模型对比

```bash
python compare_models.py your_video.mp4
python compare_models.py your_video.mp4 gemini gpt4o  # 指定模型
```

## 📊 功能对比

| 功能 | Web界面 | 完整分析 | 深度分析 | 快速分析 | 多模型对比 |
|------|---------|---------|---------|---------|-----------|
| 易用性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 智能分段 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 待办事项 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 发言人识别 | ❌ | ✅ | ❌ | ❌ | ❌ |
| 决策点检测 | ❌ | ✅ | ❌ | ❌ | ❌ |
| PDF导出 | ❌ | ✅ | ❌ | ❌ | ❌ |
| 知识库 | ❌ | ✅ | ❌ | ❌ | ❌ |
| 在线查看 | ✅ | ❌ | ❌ | ❌ | ✅ |

## 🎨 输出示例

### 完整分析输出
```
output/complete_analysis_20240309_143022/
├── basic_analysis.json      # 基础分析
├── segments.json            # 智能分段
├── action_items.json        # 待办事项
├── speakers.json            # 发言人信息
├── decisions.json           # 决策点
├── meeting_minutes.md       # 会议纪要
├── speaker_report.md        # 发言人报告
├── decision_report.md       # 决策点报告
├── timeline_report.html     # 时间轴报告
├── meeting_report.pdf       # PDF 报告
└── statistics.json          # 统计信息
```

## 🤖 支持的 AI 模型

| 模型 | 提供商 | 视频支持 | 特点 | 完整分析 |
|------|--------|----------|------|---------|
| **Gemini 2.0 Flash** | Google | ✅ 原生 | 最快，免费 | ✅ |
| **GPT-4o** | OpenAI | 🔄 帧+音频 | 强大理解 | 🚧 |
| **Claude 3.5 Sonnet** | Anthropic | 🔄 帧+音频 | 细致分析 | 🚧 |
| **Qwen2-VL** | 阿里 | ✅ 原生 | 中文优化 | 🚧 |

## 📋 已实现功能清单

### ✅ P0 - 核心功能（已完成）
- [x] 智能分段 + 时间轴
- [x] 会议纪要生成（Markdown）
- [x] 待办事项提取
- [x] Web 界面

### ✅ P1 - 重要功能（已完成）
- [x] 发言人识别
- [x] 决策点标注
- [x] PDF 导出

### ✅ P2 - 增强功能（已完成）
- [x] 知识库数据库
- [x] 历史会议搜索
- [x] 统计报告

### 🚧 P3 - 未来功能
- [ ] 情感分析
- [ ] 关键词云图
- [ ] 思维导图生成
- [ ] 智能问答
- [ ] 趋势分析

## 💡 使用场景

**企业团队**：
- 📊 周会/月会分析
- 🎯 项目讨论总结
- 📝 客户会议纪要
- 🔍 历史决策回顾

**教育培训**：
- 📚 课程内容提取
- 🎓 培训总结
- 📖 知识点整理

**个人使用**：
- 📹 视频内容总结
- 📝 笔记整理
- 🔖 重点标记

## 🔧 技术架构

```
videos-agents/
├── web/                    # Web 应用
│   ├── app.py             # Flask 后端
│   └── templates/
│       └── index.html     # 前端界面
├── analyzers/              # 多模型分析器
│   ├── gemini_analyzer.py
│   ├── gpt4o_analyzer.py
│   ├── claude_analyzer.py
│   └── qwen_analyzer.py
├── processors/             # 视频处理器
│   ├── segmenter.py       # 智能分段
│   ├── action_item_extractor.py
│   ├── speaker_diarizer.py
│   └── decision_detector.py
├── exporters/              # 导出器
│   ├── markdown_exporter.py
│   └── pdf_exporter.py
├── knowledge/              # 知识库
│   ├── database.py        # SQLite 数据库
│   └── search.py          # 搜索引擎
├── timeline_report_generator.py
├── run_web.py             # Web 启动脚本
├── analyze_complete.py    # 完整分析入口
├── analyze_meeting_deep.py
└── compare_models.py
```

## 📝 API Keys 配置

在 `.env` 文件中配置：

```bash
# Gemini (必需)
GOOGLE_API_KEY=your_key

# 以下为可选（用于多模型对比）
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
DASHSCOPE_API_KEY=your_key
```

获取 API Keys：
- Gemini: https://aistudio.google.com/app/apikey (免费)
- OpenAI: https://platform.openai.com/api-keys
- Claude: https://console.anthropic.com/
- 通义千问: https://dashscope.console.aliyun.com/

## ⚠️ 注意事项

- 视频文件限制：< 500MB
- 视频时长建议：< 1小时
- 完整分析耗时：3-8 分钟
- 需要稳定的网络连接
- PDF 导出需要安装 reportlab

## 🐛 故障排除

### Web 服务端口被占用
```bash
# 编辑 run_web.py，修改端口
app.run(debug=True, host='0.0.0.0', port=8080)  # 改为其他端口
```

### PDF 生成失败
```bash
pip install reportlab
```

### 视频上传失败
- 检查文件大小是否超过 500MB
- 检查视频格式是否支持
- 确保有足够的磁盘空间

## 📄 License

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

- GitHub: https://github.com/DouHaowen/videos-agents
- Issues: https://github.com/DouHaowen/videos-agents/issues

---

**开发完成度**: 100% ✅

所有计划功能已实现：
- ✅ P0: 智能分段、待办事项、会议纪要、时间轴
- ✅ P1: 发言人识别、决策点检测、PDF 导出
- ✅ P2: 知识库、搜索引擎
- ✅ Web 界面
- ✅ 多模型对比
