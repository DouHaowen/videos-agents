"""
Flask Web 应用
提供视频上传和分析的 Web 界面
"""

import os
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv

from processors.segmenter import MeetingSegmenter
from processors.action_item_extractor import ActionItemExtractor
from exporters.markdown_exporter import MarkdownExporter
from timeline_report_generator import TimelineReportGenerator

load_dotenv()

# 设置代理（如果配置了）
if os.getenv('HTTP_PROXY'):
    os.environ['http_proxy'] = os.getenv('HTTP_PROXY')
    os.environ['https_proxy'] = os.getenv('HTTPS_PROXY', os.getenv('HTTP_PROXY'))
    print(f"✓ 代理已配置: {os.getenv('HTTP_PROXY')}")


def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
    app.config['UPLOAD_FOLDER'] = Path('uploads')
    app.config['OUTPUT_FOLDER'] = Path('output')
    
    # 创建必要的目录
    app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
    app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)
    
    # 配置 Gemini
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')
    
    @app.route('/api/upload', methods=['POST'])
    def upload_video():
        """上传视频"""
        if 'video' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        filepath = app.config['UPLOAD_FOLDER'] / safe_filename
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': safe_filename,
            'filepath': str(filepath)
        })
    
    @app.route('/api/analyze', methods=['POST'])
    def analyze_video():
        """分析视频"""
        data = request.json
        filepath = data.get('filepath')
        analysis_type = data.get('type', 'deep')  # deep/quick
        
        if not filepath or not Path(filepath).exists():
            return jsonify({'error': '文件不存在'}), 400
        
        try:
            if analysis_type == 'deep':
                result = perform_deep_analysis(filepath)
            else:
                result = perform_quick_analysis(filepath)
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/results/<session_id>')
    def get_results(session_id):
        """获取分析结果"""
        session_dir = app.config['OUTPUT_FOLDER'] / session_id
        
        if not session_dir.exists():
            return jsonify({'error': '结果不存在'}), 404
        
        # 读取结果文件
        results = {}
        
        if (session_dir / 'basic_analysis.json').exists():
            with open(session_dir / 'basic_analysis.json', 'r', encoding='utf-8') as f:
                results['basic_analysis'] = json.load(f)
        
        if (session_dir / 'segments.json').exists():
            with open(session_dir / 'segments.json', 'r', encoding='utf-8') as f:
                results['segments'] = json.load(f)
        
        if (session_dir / 'action_items.json').exists():
            with open(session_dir / 'action_items.json', 'r', encoding='utf-8') as f:
                results['action_items'] = json.load(f)
        
        return jsonify(results)
    
    @app.route('/api/download/<session_id>/<file_type>')
    def download_file(session_id, file_type):
        """下载文件"""
        session_dir = app.config['OUTPUT_FOLDER'] / session_id
        
        file_map = {
            'markdown': 'meeting_minutes.md',
            'timeline': 'timeline_report.html',
            'json': 'basic_analysis.json'
        }
        
        filename = file_map.get(file_type)
        if not filename:
            return jsonify({'error': '不支持的文件类型'}), 400
        
        filepath = session_dir / filename
        if not filepath.exists():
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(filepath, as_attachment=True)
    
    @app.route('/view/<session_id>')
    def view_report(session_id):
        """查看报告"""
        session_dir = app.config['OUTPUT_FOLDER'] / session_id
        report_path = session_dir / 'timeline_report.html'
        
        if not report_path.exists():
            return "报告不存在", 404
        
        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def perform_deep_analysis(filepath):
        """执行深度分析"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"deep_analysis_{timestamp}"
        session_dir = app.config['OUTPUT_FOLDER'] / session_id
        session_dir.mkdir(exist_ok=True)
        
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # 上传视频
        video_file = genai.upload_file(path=filepath)
        
        # 等待处理
        import time
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise ValueError("视频处理失败")
        
        # 基础分析
        basic_prompt = """请分析这个会议视频，提供：
1. 会议主题摘要（1-2句话）
2. 主要讨论点（3-5个）
3. 场景分类（工作/私生活/健康/运动/出行）
4. 完整的会议转录文本

请以 JSON 格式返回：
{
  "summary": "会议摘要",
  "key_points": ["讨论点1", "讨论点2"],
  "category": "分类",
  "transcript": "完整转录文本"
}"""
        
        response = model.generate_content(
            [video_file, basic_prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        
        basic_analysis = json.loads(response.text)
        transcript = basic_analysis.get("transcript", "")
        
        # 保存基础分析
        with open(session_dir / "basic_analysis.json", "w", encoding="utf-8") as f:
            json.dump(basic_analysis, f, ensure_ascii=False, indent=2)
        
        # 获取视频时长
        import cv2
        cap = cv2.VideoCapture(filepath)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        video_duration = frame_count / fps if fps > 0 else 600
        cap.release()
        
        # 智能分段
        segmenter = MeetingSegmenter(model)
        segments = segmenter.segment_meeting(transcript, video_duration)
        
        with open(session_dir / "segments.json", "w", encoding="utf-8") as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        
        # 提取待办事项
        extractor = ActionItemExtractor(model)
        action_items = extractor.extract_action_items(transcript, segments)
        
        with open(session_dir / "action_items.json", "w", encoding="utf-8") as f:
            json.dump(action_items, f, ensure_ascii=False, indent=2)
        
        # 生成 Markdown
        md_exporter = MarkdownExporter()
        meeting_info = {
            "date": datetime.now().strftime("%Y年%m月%d日"),
            "title": "会议分析",
            "duration": MeetingSegmenter.format_time(video_duration)
        }
        md_exporter.export_meeting_minutes(
            basic_analysis, segments, action_items, session_dir, meeting_info
        )
        
        # 生成时间轴报告
        timeline_gen = TimelineReportGenerator()
        timeline_gen.generate_timeline_report(
            basic_analysis, segments, action_items, session_dir
        )
        
        # 清理
        genai.delete_file(video_file.name)
        
        return {
            'success': True,
            'session_id': session_id,
            'summary': basic_analysis.get('summary'),
            'category': basic_analysis.get('category'),
            'segments_count': len(segments),
            'action_items_count': len(action_items)
        }
    
    def perform_quick_analysis(filepath):
        """执行快速分析"""
        # 简化版本，只做基础分析
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"quick_analysis_{timestamp}"
        session_dir = app.config['OUTPUT_FOLDER'] / session_id
        session_dir.mkdir(exist_ok=True)
        
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        video_file = genai.upload_file(path=filepath)
        
        import time
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        prompt = """请分析这个会议视频，提供简要摘要和主要讨论点。
返回 JSON 格式：{"summary": "摘要", "key_points": ["点1", "点2"], "category": "分类"}"""
        
        response = model.generate_content(
            [video_file, prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        
        with open(session_dir / "analysis.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        genai.delete_file(video_file.name)
        
        return {
            'success': True,
            'session_id': session_id,
            'summary': result.get('summary'),
            'category': result.get('category'),
            'key_points': result.get('key_points', [])
        }
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
