"""
文件管理工具模块
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class FileManager:
    """文件管理器，负责所有文件读写操作"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.encoding = 'utf-8'

    def ensure_dir(self, dir_path: str) -> Path:
        """确保目录存在"""
        full_path = self.project_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    def read_json(self, file_path: str) -> Optional[Dict]:
        """读取JSON文件"""
        full_path = self.project_path / file_path
        if not full_path.exists():
            return None
        with open(full_path, 'r', encoding=self.encoding) as f:
            return json.load(f)

    def write_json(self, file_path: str, data: Dict, indent: int = 2):
        """写入JSON文件"""
        full_path = self.project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding=self.encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    def read_text(self, file_path: str) -> Optional[str]:
        """读取文本文件"""
        full_path = self.project_path / file_path
        if not full_path.exists():
            return None
        with open(full_path, 'r', encoding=self.encoding) as f:
            return f.read()

    def write_text(self, file_path: str, content: str):
        """写入文本文件"""
        full_path = self.project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding=self.encoding) as f:
            f.write(content)

    def read_markdown(self, file_path: str) -> Optional[str]:
        """读取Markdown文件"""
        return self.read_text(file_path)

    def write_markdown(self, file_path: str, content: str):
        """写入Markdown文件"""
        self.write_text(file_path, content)

    def append_text(self, file_path: str, content: str):
        """追加文本到文件"""
        full_path = self.project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'a', encoding=self.encoding) as f:
            f.write(content)

    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        return (self.project_path / file_path).exists()

    def list_files(self, dir_path: str, pattern: str = '*') -> list:
        """列出目录下的文件"""
        full_path = self.project_path / dir_path
        if not full_path.exists():
            return []
        return [str(p.relative_to(self.project_path)) for p in full_path.glob(pattern)]

    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        full_path = self.project_path / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def get_chapter_files(self) -> list:
        """获取所有章节文件，按章节号排序"""
        chapters_dir = self.project_path / 'chapters'
        if not chapters_dir.exists():
            return []

        chapter_files = []
        for f in chapters_dir.glob('chapter_*.md'):
            # 提取章节号
            try:
                num = int(f.stem.split('_')[1])
                chapter_files.append((num, str(f.relative_to(self.project_path))))
            except (IndexError, ValueError):
                continue

        return [f for _, f in sorted(chapter_files)]

    def create_chapter_filename(self, chapter_num: int, title: str = None) -> str:
        """创建章节文件名"""
        if title:
            # 清理标题中的非法字符
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '一-龥'))
            safe_title = safe_title[:30]  # 限制长度
            return f"chapters/chapter_{chapter_num:03d}_{safe_title}.md"
        return f"chapters/chapter_{chapter_num:03d}.md"

    def backup_project(self, backup_dir: str):
        """备份整个项目"""
        import shutil
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = Path(backup_dir) / f"backup_{timestamp}"
        shutil.copytree(self.project_path, backup_path)
        return str(backup_path)
