# 会议视频分析系统

一个面向日常团队会议的 AI 分析系统。当前主链路已经升级为：

`上传视频 -> 提取音频 -> OpenAI 转录 -> Gemini 分析文本 -> 生成纪要/待办/决策 -> 沉淀历史和全局任务中心`

它的目标不是只做一次性总结，而是持续记录会议内容，追踪老板要求、任务进展和跨会议状态变化。

## 当前核心能力

### 1. 完整会议分析

- 上传会议视频
- 自动提取音频
- 调用 OpenAI 语音转录接口生成文字和发言片段
- 调用 Gemini 对转录文本做结构化分析
- 提取老板要求、员工汇报、风险、下一步动作
- 识别议题、待办事项、发言人、关键决策

### 2. 统一 Web 工作台

- 单页联动操作，不再跳转割裂页面
- 左侧历史记录，右侧当前会议详情
- 页内查看员工汇报、议题时间轴、待办事项、发言人、决策、完整报告
- 支持下载 Markdown、PDF、结构化转录

### 3. 历史记录沉淀

- 每次分析都会保留历史
- 支持回看历史会议
- 支持删除历史记录
- 历史信息写入 SQLite 数据库

### 4. 全局任务中心

- 把每次会议的待办事项沉淀成全局任务
- 记录任务来源会议、提出日期、负责人、优先级、截止日期
- 记录最近提及会议
- 如果后续会议提到任务已完成或阻塞，会自动回写状态
- 展示完成会议和完成日期

### 5. 老板要求长期追踪

- 从会议中提取老板要求
- 沉淀为长期要求库
- 和任务中心一起形成持续记忆层

## 当前主流程

1. 用户上传会议视频
2. 系统从视频中提取音频
3. 使用 OpenAI 转录接口生成文字和发言片段
4. 使用 Gemini 对转录文本做结构化理解
5. 生成：
   - 会议标题
   - 摘要
   - 关键点
   - 管理视角总结
   - 议题分段
   - 待办事项
   - 发言人汇总
   - 决策点
6. 导出 Markdown / HTML / PDF / JSON
7. 保存会议历史到 SQLite
8. 同步更新全局任务中心和老板要求库
9. 在下一次会议中继续利用历史任务做状态联动

## Web 界面

当前 Web 端分成两个主要视图：

### 会议工作台

用于：

- 上传视频
- 启动完整分析
- 查看本次会议结果
- 下载分析产物
- 浏览和删除历史记录

### 全局任务中心

用于：

- 查看所有历史会议沉淀出的任务
- 查看任务状态分布
- 查看任务的来源会议和提出日期
- 查看截止日期
- 查看完成会议和完成日期
- 查看最近的任务更新记录
- 查看老板要求追踪

## 输出文件

每次完整分析都会在 `output/<session_id>/` 下生成结果，常见文件包括：

- `basic_analysis.json`
- `transcription.json`
- `structured_transcript.json`
- `participant_roles.json`
- `segments.json`
- `action_items.json`
- `speakers.json`
- `decisions.json`
- `meeting_minutes.md`
- `speaker_report.md`
- `decision_report.md`
- `timeline_report.html`
- `meeting_report.pdf`
- `statistics.json`

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

在 `.env` 中至少配置：

```bash
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
```

说明：

- `GOOGLE_API_KEY`：用于 Gemini 文本分析
- `OPENAI_API_KEY`：用于音频转录

### 3. 启动 Web 服务

推荐直接使用：

```bash
./start_web.sh
```

也可以手动启动：

```bash
source venv/bin/activate
python run_web.py
```

启动后，浏览器打开：

- [http://localhost:8080](http://localhost:8080)

如果 `8080` 被占用，程序会自动尝试 `8081`、`8082`、`5001` 等端口。

## 命令行入口

### 完整分析

```bash
python analyze_complete.py your_video.mp4
```

### 深度分析入口

```bash
python analyze_meeting_deep.py your_video.mp4
```

### 统一分析入口

```bash
python analyze_with_gemini.py your_video.mp4
```

说明：

- 当前这些入口都已统一到完整分析链路
- 不再保留“快速概览”模式

## 主要模块

```text
videos-agents/
├── web/                         # Flask Web 应用
│   ├── app.py
│   └── templates/index.html
├── processors/
│   ├── audio_transcriber.py     # 音频提取与 OpenAI 转录
│   ├── structured_transcript.py # 基于文本的结构化分析
│   ├── meeting_insights.py      # 老板要求/员工汇报/风险/下一步
│   ├── task_tracker.py          # 跨会议任务进展识别
│   ├── segmenter.py
│   ├── action_item_extractor.py
│   ├── speaker_diarizer.py
│   └── decision_detector.py
├── exporters/
│   ├── markdown_exporter.py
│   └── pdf_exporter.py
├── knowledge/
│   ├── database.py              # SQLite 数据库与长期记忆层
│   └── search.py
├── meeting_pipeline.py          # 统一分析编排
├── analyze_complete.py
├── analyze_meeting_deep.py
├── analyze_with_gemini.py
├── compare_models.py
├── run_web.py
└── start_web.sh
```

## 数据库中目前保存的内容

SQLite 数据库当前会保存：

- `meetings`：会议主表
- `segments`：议题分段
- `action_items`：单次会议待办事项
- `speakers`：发言人汇总
- `participants`：参与者与角色
- `decisions`：决策点
- `task_memory`：全局任务总表
- `task_updates`：任务更新历史
- `requirement_memory`：老板要求库
- `requirement_updates`：老板要求更新历史

## 适合的使用场景

- 老板和团队的日常例会
- 项目进度汇报
- 周会 / 月会纪要
- 持续追踪老板交代的事项
- 跟踪任务是否在后续会议中推进或完成

## 当前已知边界

### 1. 任务状态联动是第一版

系统已经能自动识别“推进中 / 已完成 / 阻塞 / 重新打开”，但它仍基于模型理解，不是完全规则化引擎。首次投入真实会议时，建议人工抽查。

### 2. 视觉信息利用较少

当前主链路已经从“视频直分析”切到“音频转录 + 文本分析”，因此它更擅长会议语义提炼，但对屏幕演示内容、视觉画面信息利用较少。

### 3. Gemini SDK 后续建议迁移

当前项目仍在使用 `google.generativeai`，后续建议迁移到 `google.genai`。

## 后续适合继续增强的方向

1. 任务搜索和筛选
2. 项目维度聚合
3. 任务手动修正和审批
4. 更精细的任务匹配与去重
5. Gemini SDK 迁移

## 相关说明文档

- [PROJECT_UPDATE_2026-03-10.md](/Users/saita/saita/videos-agnets/PROJECT_UPDATE_2026-03-10.md)

