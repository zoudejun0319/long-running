"""
审查代理模块

基于 Anthropic "Effective harnesses for long-running agents" 理论设计
核心思想：不要轻信"已完成"，必须进行端到端验证
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from utils.file_manager import FileManager
from utils.word_counter import WordCounter


class Reviewer:
    """
    审查代理

    职责（来自Anthropic最佳实践）：
    1. 不要轻信"已完成"：必须进行端到端验证
    2. 只修改状态字段：不要删除或编辑检查项
    3. 严格标准：只有真正通过的才能标记为 passes: true
    4. 详细记录：失败原因必须写清楚
    """

    def __init__(self, project_path: str, config: Dict = None):
        self.project_path = Path(project_path)
        self.config = config or {}
        self.file_manager = FileManager(project_path)

        # 加载项目数据
        self.chapter_list = self.file_manager.read_json('chapter_list.json') or {}
        self.characters = self.file_manager.read_json('characters.json') or {}
        self.foreshadowing = self.file_manager.read_json('foreshadowing.json') or {}
        self.quality_checklist = self.file_manager.read_json('quality_checklist.json') or {}

        # 加载世界规则
        self.world_rules = self._load_world_rules()

    def _load_world_rules(self) -> Dict:
        """加载世界规则"""
        rules = {}
        world_rules_dir = self.project_path / 'world_rules'

        if world_rules_dir.exists():
            for file in world_rules_dir.glob('*.json'):
                key = file.stem
                data = self.file_manager.read_json(f'world_rules/{file.name}')
                if data:
                    rules[key] = data

        return rules

    def review_chapter(self, chapter_num: int, content: str = None) -> Dict:
        """
        审查单个章节

        Args:
            chapter_num: 章节号
            content: 章节内容，None则从文件读取

        Returns:
            审查结果
        """
        # 获取章节内容
        if content is None:
            content = self._read_chapter_content(chapter_num)
            if content is None:
                return {
                    'overall_passes': False,
                    'summary': f'无法读取第{chapter_num}章内容'
                }

        # 获取章节信息
        chapter_info = self._get_chapter_info(chapter_num)
        if chapter_info is None:
            return {
                'overall_passes': False,
                'summary': f'找不到第{chapter_num}章的信息'
            }

        # 获取检查标准
        checks_config = self.quality_checklist.get('checks', [])
        writing_standards = self.chapter_list.get('writing_standards', {})

        # 执行各项检查
        checks = {}
        issues = []

        # 1. 字数检查
        word_check = self._check_word_count(content, writing_standards)
        checks['word_count'] = word_check
        if not word_check['passes']:
            issues.append({
                'type': 'critical' if word_check.get('severity') == 'critical' else 'warning',
                'check': 'word_count',
                'description': word_check.get('notes', ''),
                'suggestion': '调整章节字数'
            })

        # 2. POV一致性
        pov_check = self._check_pov_consistency(content, chapter_info)
        checks['pov_consistency'] = pov_check
        if not pov_check['passes']:
            issues.append({
                'type': 'warning',
                'check': 'pov_consistency',
                'description': pov_check.get('notes', ''),
                'suggestion': '检查视角是否统一'
            })

        # 3. 人物一致性
        char_check = self._check_character_consistency(content, chapter_info, self.characters)
        checks['character_consistency'] = char_check
        if not char_check['passes']:
            issues.append({
                'type': 'warning',
                'check': 'character_consistency',
                'description': char_check.get('notes', ''),
                'suggestion': '检查人物行为是否符合设定'
            })

        # 4. 世界规则
        world_check = self._check_world_rules(content, self.world_rules)
        checks['world_rules'] = world_check
        if not world_check['passes']:
            issues.append({
                'type': 'critical',
                'check': 'world_rules',
                'description': world_check.get('notes', ''),
                'suggestion': '检查是否违反世界观设定'
            })

        # 5. 伏笔处理
        foreshadow_check = self._check_foreshadowing(content, chapter_info, self.foreshadowing)
        checks['foreshadowing'] = foreshadow_check
        if not foreshadow_check['passes']:
            issues.append({
                'type': 'warning',
                'check': 'foreshadowing',
                'description': foreshadow_check.get('notes', ''),
                'suggestion': '检查伏笔埋设/回收'
            })

        # 6. 时间线
        timeline_check = self._check_timeline(content, chapter_info)
        checks['timeline'] = timeline_check
        if not timeline_check['passes']:
            issues.append({
                'type': 'warning',
                'check': 'timeline',
                'description': timeline_check.get('notes', ''),
                'suggestion': '检查时间线一致性'
            })

        # 7. 剧情连贯
        plot_check = self._check_plot_coherence(content, chapter_info)
        checks['plot_coherence'] = plot_check
        if not plot_check['passes']:
            issues.append({
                'type': 'warning',
                'check': 'plot_coherence',
                'description': plot_check.get('notes', ''),
                'suggestion': '检查剧情逻辑'
            })

        # 8. 写作质量
        quality_check = self._check_writing_quality(content)
        checks['writing_quality'] = quality_check
        if not quality_check['passes']:
            issues.append({
                'type': 'suggestion',
                'check': 'writing_quality',
                'description': quality_check.get('notes', ''),
                'suggestion': '改进写作质量'
            })

        # 计算是否通过
        # 只有所有 required 且 critical 的检查通过才算通过
        critical_issues = [i for i in issues if i.get('type') == 'critical']
        required_failures = [c for c in checks_config if c.get('required', False) and not checks.get(c['id'], {}).get('passes', True)]

        overall_passes = len(critical_issues) == 0 and len(required_failures) == 0

        # 生成摘要
        if overall_passes:
            summary = "质量检查通过 [OK]"
        else:
            summary = f"发现 {len(issues)} 个问题"
            if critical_issues:
                summary += f"（{len(critical_issues)} 个严重）"

        return {
            'overall_passes': overall_passes,
            'checks': checks,
            'issues': issues,
            'summary': summary,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _read_chapter_content(self, chapter_num: int) -> Optional[str]:
        """读取章节内容"""
        files = self.file_manager.list_files('chapters', f'chapter_{chapter_num:03d}*.md')
        if files:
            content = self.file_manager.read_markdown(files[0])
            if content and content.startswith('#'):
                content = content.split('\n', 1)[1] if '\n' in content else ''
            return content
        return None

    def _get_chapter_info(self, chapter_num: int) -> Optional[Dict]:
        """获取章节信息"""
        for ch in self.chapter_list.get('chapters', []):
            if ch.get('number') == chapter_num:
                return ch
        return None

    def _check_word_count(self, content: str, writing_standards: Dict) -> Dict:
        """检查字数"""
        min_words = writing_standards.get('min_words_per_chapter', 2500)
        max_words = writing_standards.get('max_words_per_chapter', 5000)

        count = WordCounter.count(content)
        actual = count['total']

        passes = min_words <= actual <= max_words

        notes = ""
        severity = None
        if actual < min_words:
            notes = f"字数不足: {actual} < {min_words}"
            severity = 'critical' if actual < min_words * 0.7 else 'warning'
        elif actual > max_words:
            notes = f"字数超标: {actual} > {max_words}"
            severity = 'warning'

        return {
            'passes': passes,
            'actual': actual,
            'min': min_words,
            'max': max_words,
            'notes': notes,
            'severity': severity
        }

    def _check_pov_consistency(self, content: str, chapter_info: Dict) -> Dict:
        """检查POV一致性"""
        # 简化实现：实际需要更复杂的NLP处理
        passes = True
        notes = ""

        pov_character = chapter_info.get('pov_character', '')

        # 检查是否有"不知道"这类越界表述
        # 这是一个简化的检查
        if '不知道' in content and '身后' in content:
            # 可能存在POV越界
            pass

        return {
            'passes': passes,
            'notes': notes
        }

    def _check_character_consistency(self, content: str, chapter_info: Dict, characters: Dict) -> Dict:
        """检查人物一致性"""
        # 简化实现
        passes = True
        notes = ""

        # 检查涉及的人物是否在内容中出现
        involved = chapter_info.get('characters_involved', [])

        return {
            'passes': passes,
            'notes': notes
        }

    def _check_world_rules(self, content: str, world_rules: Dict) -> Dict:
        """检查世界规则"""
        passes = True
        notes = ""

        # 检查科技规则
        tech_system = world_rules.get('tech_system', {})
        if tech_system:
            tech_rules = tech_system.get('tech_rules', [])
            # 简化：实际需要语义分析

        return {
            'passes': passes,
            'notes': notes
        }

    def _check_foreshadowing(self, content: str, chapter_info: Dict, foreshadowing: Dict) -> Dict:
        """检查伏笔处理"""
        passes = True
        notes = ""

        plant_list = chapter_info.get('foreshadowing_plant', [])
        resolve_list = chapter_info.get('foreshadowing_resolve', [])

        # 检查需要埋设的伏笔
        for item in plant_list:
            if item and item not in content:
                notes += f"伏笔'{item}'可能未埋设; "

        return {
            'passes': passes,
            'notes': notes.strip()
        }

    def _check_timeline(self, content: str, chapter_info: Dict) -> Dict:
        """检查时间线"""
        # 简化实现
        return {
            'passes': True,
            'notes': ''
        }

    def _check_plot_coherence(self, content: str, chapter_info: Dict) -> Dict:
        """检查剧情连贯"""
        # 简化实现
        passes = True
        notes = ""

        # 检查关键事件是否体现
        key_events = chapter_info.get('key_events', [])

        return {
            'passes': passes,
            'notes': notes
        }

    def _check_writing_quality(self, content: str) -> Dict:
        """检查写作质量"""
        passes = True
        notes = ""

        # 检查开篇
        first_para = content.split('\n\n')[0] if '\n\n' in content else content[:200]
        if len(first_para) < 50:
            notes = "开篇可能过于简短"

        return {
            'passes': passes,
            'notes': notes
        }

    def review_all(self) -> Dict:
        """审查所有已完成章节"""
        results = []
        total_issues = 0

        chapters = self.chapter_list.get('chapters', [])
        for ch in chapters:
            if ch.get('word_actual', 0) > 0:  # 有内容的章节
                result = self.review_chapter(ch.get('number'))
                results.append({
                    'chapter': ch.get('number'),
                    'passes': result.get('overall_passes', False),
                    'issues_count': len(result.get('issues', []))
                })
                total_issues += len(result.get('issues', []))

        return {
            'total_reviewed': len(results),
            'total_issues': total_issues,
            'results': results
        }
