# 会议视频分析系统 - 多模型对比版

使用多个顶级 AI 模型分析同一个会议视频，对比它们的理解能力。

## 支持的模型

| 模型 | 提供商 | 视频支持 | 特点 |
|------|--------|----------|------|
| **Gemini 2.0 Flash** | Google | ✅ 原生 | 最快，直接处理视频 |
| **GPT-4o** | OpenAI | 🔄 帧+音频 | 强大的多模态理解 |
| **Claude 3.5 Sonnet** | Anthropic | 🔄 帧+音频 | 细致的文本分析 |
| **Qwen2-VL** | 阿里 | ✅ 原生 | 中文优化，支持视频 |

## 安装

```bash
pip install -r requirements.txt
```

## 配置 API Keys

1. 复制配置文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API Keys：

```bash
# Gemini (免费): https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_key

# OpenAI: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_key

# Claude: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_key

# 通义千问: https://dashscope.console.aliyun.com/
DASHSCOPE_API_KEY=your_key
```

## 使用方法

### 1. 单模型分析（快速）

```bash
# 使用 Gemini（推荐，最快）
python analyze_with_gemini.py your_video.mp4
```

### 2. 多模型对比（完整）

```bash
# 使用所有配置的模型
python compare_models.py your_video.mp4

# 只对比指定模型
python compare_models.py your_video.mp4 gemini gpt4o
python compare_models.py your_video.mp4 gemini qwen
```

## 输出结果

### 单模型输出
```
output/meeting_20240309_143022/
├── analysis.json      # 结构化分析结果
└── report.html        # 可视化报告
```

### 多模型对比输出
```
output/comparison_20240309_143022/
├── comparison.html    # 对比报告（主页）
├── gemini/
│   ├── analysis.json
│   └── report.html
├── gpt4o/
│   ├── analysis.json
│   ├── frames/        # 提取的视频帧
│   └── report.html
├── claude/
│   ├── analysis.json
│   ├── frames/
│   └── report.html
└── qwen/
    ├── analysis.json
    └── report.html
```

## 对比维度

系统会从以下维度对比各模型：

- ⏱️ **处理速度** - 完整分析耗时
- 🏷️ **场景分类** - 分类准确性
- 📝 **内容理解** - 摘要质量
- 💡 **细节捕捉** - 讨论点提取
- ✅ **行动项识别** - 任务提取能力

## 模型特点对比

### Gemini 2.0 Flash
- ✅ 原生视频支持，无需预处理
- ✅ 速度最快（通常 10-30 秒）
- ✅ 免费额度充足
- ⚠️ 视频上传需要时间

### GPT-4o
- ✅ 强大的多模态理解
- ✅ 优秀的中文支持
- ⚠️ 需要提取帧和音频（较慢）
- ⚠️ 成本较高

### Claude 3.5 Sonnet
- ✅ 细致的文本分析
- ✅ 安全性好
- ⚠️ 需要提取帧和音频
- ⚠️ 图片数量限制（5张）
- ⚠️ 无语音 API（需借用 Whisper）

### Qwen2-VL
- ✅ 原生视频支持
- ✅ 中文优化
- ✅ 国内访问快
- ⚠️ 需要阿里云账号

## 支持的视频格式

MP4, MOV, AVI, FLV, MPG, MPEG, WMV, 3GPP

## 注意事项

- 视频文件建议 < 500MB
- 视频时长建议 < 1小时
- 确保网络连接稳定
- 首次运行会安装 ffmpeg（moviepy 依赖）

## 成本估算

以 10 分钟会议视频为例：

- **Gemini**: 免费（每天 1500 次请求）
- **GPT-4o**: ~$0.10-0.20（Whisper + Vision）
- **Claude**: ~$0.15-0.25（需借用 Whisper）
- **Qwen**: 按阿里云计费

## 故障排除

### moviepy 安装失败
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# 下载 ffmpeg 并添加到 PATH
```

### API 调用失败
- 检查 API Key 是否正确
- 检查账户余额/配额
- 检查网络连接
