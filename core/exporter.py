"""
导出功能模块
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from utils.file_manager import FileManager
from utils.word_counter import WordCounter


class Exporter:
    """
    导出器

    支持导出格式：
    - txt: 纯文本
    - markdown: Markdown格式
    - json: JSON格式（包含元数据）
    - html: HTML格式
    """

    def __init__(self, project_path: str, config: Dict = None):
        self.project_path = Path(project_path)
        self.config = config or {}
        self.file_manager = FileManager(project_path)

        # 加载项目数据
        self.chapter_list = self.file_manager.read_json('chapter_list.json') or {}

    def export(self, format: str = 'txt', output_path: str = None,
               include_metadata: bool = True) -> Dict:
        """
        导出小说

        Args:
            format: 导出格式 ('txt', 'markdown', 'json', 'html')
            output_path: 输出路径，None则自动生成
            include_metadata: 是否包含元数据

        Returns:
            导出结果
        """
        # 获取所有章节
        chapters = self._get_all_chapters()

        if not chapters:
            return {
                'success': False,
                'message': '没有已完成的章节可导出'
            }

        # 生成输出路径
        if output_path is None:
            title = self.chapter_list.get('meta', {}).get('title', '未命名')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = self._get_extension(format)
            output_path = self.project_path / 'exports' / f"{title}_{timestamp}.{ext}"
        else:
            output_path = Path(output_path)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 根据格式导出
        if format == 'txt':
            content = self._export_txt(chapters, include_metadata)
        elif format == 'markdown':
            content = self._export_markdown(chapters, include_metadata)
        elif format == 'json':
            content = self._export_json(chapters, include_metadata)
        elif format == 'html':
            content = self._export_html(chapters, include_metadata)
        else:
            return {
                'success': False,
                'message': f'不支持的格式: {format}'
            }

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 统计信息
        stats = self._calculate_stats(chapters)

        return {
            'success': True,
            'output_path': str(output_path),
            'format': format,
            'chapters_exported': len(chapters),
            'total_words': stats['total_words'],
            'file_size': len(content.encode('utf-8'))
        }

    def _get_all_chapters(self) -> List[Dict]:
        """获取所有已完成的章节"""
        chapters = []

        # 获取章节文件
        chapter_files = self.file_manager.get_chapter_files()

        for file_path in chapter_files:
            content = self.file_manager.read_markdown(file_path)
            if content:
                # 提取章节号
                filename = Path(file_path).stem
                try:
                    chapter_num = int(filename.split('_')[1])
                except (IndexError, ValueError):
                    continue

                # 检查章节状态
                chapter_info = None
                for ch in self.chapter_list.get('chapters', []):
                    if ch.get('number') == chapter_num:
                        chapter_info = ch
                        break

                # 只导出有内容的章节
                if chapter_info and chapter_info.get('word_actual', 0) > 0:
                    chapters.append({
                        'number': chapter_num,
                        'title': chapter_info.get('title', f'第{chapter_num}章'),
                        'content': content,
                        'word_actual': chapter_info.get('word_actual', 0)
                    })

        # 按章节号排序
        chapters.sort(key=lambda x: x['number'])

        return chapters

    def _get_extension(self, format: str) -> str:
        """获取文件扩展名"""
        return {
            'txt': 'txt',
            'markdown': 'md',
            'json': 'json',
            'html': 'html'
        }.get(format, 'txt')

    def _export_txt(self, chapters: List[Dict], include_metadata: bool) -> str:
        """导出为纯文本"""
        lines = []
        meta = self.chapter_list.get('meta', {})
        status = self.chapter_list.get('status', {})

        # 添加元数据
        if include_metadata:
            lines.append(f"《{meta.get('title', '未命名')}》")
            lines.append("")
            lines.append(f"类型: {meta.get('genre', '')}")
            lines.append(f"字数: {status.get('completed_words', 0):,}")
            lines.append(f"章节: {len(chapters)}")
            lines.append("")
            lines.append("=" * 50)
            lines.append("")

        # 添加章节内容
        for chapter in chapters:
            lines.append(chapter['title'])
            lines.append("")
            # 移除markdown标记
            content = chapter['content']
            if content.startswith('#'):
                content = content.split('\n', 1)[1] if '\n' in content else ''
            lines.append(content.strip())
            lines.append("")
            lines.append("-" * 30)
            lines.append("")

        return '\n'.join(lines)

    def _export_markdown(self, chapters: List[Dict], include_metadata: bool) -> str:
        """导出为Markdown"""
        lines = []
        meta = self.chapter_list.get('meta', {})
        status = self.chapter_list.get('status', {})

        # 添加元数据
        if include_metadata:
            lines.append(f"# 《{meta.get('title', '未命名')}》")
            lines.append("")
            lines.append(f"> 类型: {meta.get('genre', '')}  ")
            lines.append(f"> 字数: {status.get('completed_words', 0):,}  ")
            lines.append(f"> 章节: {len(chapters)}  ")
            lines.append("")
            lines.append("---")
            lines.append("")

        # 目录
        lines.append("## 目录")
        lines.append("")
        for chapter in chapters:
            lines.append(f"- [{chapter['title']}](#chapter-{chapter['number']})")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 添加章节内容
        for chapter in chapters:
            lines.append(f'<a name="chapter-{chapter["number"]}"></a>')
            lines.append("")
            lines.append(chapter['content'])
            lines.append("")
            lines.append("---")
            lines.append("")

        return '\n'.join(lines)

    def _export_json(self, chapters: List[Dict], include_metadata: bool) -> str:
        """导出为JSON"""
        meta = self.chapter_list.get('meta', {})
        status = self.chapter_list.get('status', {})

        data = {}

        if include_metadata:
            data['meta'] = meta
            data['status'] = status

        data['chapters'] = [
            {
                'number': ch['number'],
                'title': ch['title'],
                'content': ch['content'],
                'word_count': ch.get('word_actual', 0)
            }
            for ch in chapters
        ]

        data['export_info'] = {
            'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_chapters': len(chapters),
            'total_words': sum(ch.get('word_actual', 0) for ch in chapters)
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    def _export_html(self, chapters: List[Dict], include_metadata: bool) -> str:
        """导出为HTML"""
        meta = self.chapter_list.get('meta', {})
        status = self.chapter_list.get('status', {})
        title = meta.get('title', '未命名')

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', 'SimSun', serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f9f9f9;
        }}
        h1 {{
            text-align: center;
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        .meta {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        .toc {{
            background: #fff;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .toc h2 {{
            margin-top: 0;
        }}
        .toc ul {{
            list-style: none;
            padding: 0;
            columns: 3;
        }}
        .toc a {{
            color: #0066cc;
            text-decoration: none;
        }}
        .chapter {{
            background: #fff;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .chapter h2 {{
            color: #333;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .chapter-content {{
            text-indent: 2em;
        }}
        hr {{
            border: none;
            border-top: 1px dashed #ccc;
            margin: 40px 0;
        }}
    </style>
</head>
<body>
    <h1>《{title}》</h1>
"""

        if include_metadata:
            html += f"""
    <div class="meta">
        类型: {meta.get('genre', '')} |
        字数: {status.get('completed_words', 0):,} |
        章节: {len(chapters)}
    </div>
"""

        # 目录
        html += """
    <div class="toc">
        <h2>目录</h2>
        <ul>
"""
        for chapter in chapters:
            html += f'            <li><a href="#chapter-{chapter["number"]}">{chapter["title"]}</a></li>\n'
        html += """        </ul>
    </div>
"""

        # 章节
        for chapter in chapters:
            content = chapter['content']
            if content.startswith('#'):
                content = content.split('\n', 1)[1] if '\n' in content else ''

            # 转换换行为段落
            paragraphs = content.strip().split('\n\n')
            content_html = '\n'.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())

            html += f"""
    <div class="chapter" id="chapter-{chapter['number']}">
        <h2>{chapter['title']}</h2>
        <div class="chapter-content">
{content_html}
        </div>
    </div>
    <hr>
"""

        html += """
</body>
</html>
"""

        return html

    def _calculate_stats(self, chapters: List[Dict]) -> Dict:
        """计算统计信息"""
        total_words = sum(ch.get('word_actual', 0) for ch in chapters)

        return {
            'total_words': total_words,
            'chapter_count': len(chapters),
            'average_per_chapter': total_words / len(chapters) if chapters else 0
        }
