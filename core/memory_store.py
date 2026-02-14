"""
全局记忆库模块

核心功能：追踪整个小说的关键信息，支持跨章节一致性检查
解决痛点：长篇小说容易出现前后矛盾，需要一个"记忆系统"
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class MemoryStore:
    """
    全局记忆库

    追踪内容：
    1. 人物状态变化（位置、关系、能力）
    2. 关键事件记录
    3. 时间线
    4. 物品/道具位置
    5. 伏笔状态（已埋设/已回收）
    6. 世界状态变化
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.memory_file = self.project_path / 'memory_store.json'
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict:
        """加载记忆库"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._create_empty_memory()

    def _create_empty_memory(self) -> Dict:
        """创建空记忆库结构"""
        return {
            'meta': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_chapters_tracked': 0
            },
            'characters': {},  # 人物状态追踪
            'timeline': [],     # 时间线事件
            'foreshadowing': {
                'planted': [],   # 已埋设的伏笔
                'resolved': []   # 已回收的伏笔
            },
            'items': {},        # 物品位置追踪
            'locations': {},    # 地点状态追踪
            'world_state': {},  # 世界状态
            'chapter_summaries': {},  # 章节摘要索引
            'inconsistencies': []  # 发现的不一致记录
        }

    def save(self):
        """保存记忆库"""
        self.memory['meta']['last_updated'] = datetime.now().isoformat()
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    # ========== 人物状态追踪 ==========

    def update_character_state(self, char_id: str, chapter: int,
                                state_update: Dict):
        """
        更新人物状态

        Args:
            char_id: 人物ID
            chapter: 章节号
            state_update: 状态更新（位置、关系、能力等）
        """
        if char_id not in self.memory['characters']:
            self.memory['characters'][char_id] = {
                'history': [],
                'current_state': {}
            }

        char_data = self.memory['characters'][char_id]

        # 记录历史状态
        char_data['history'].append({
            'chapter': chapter,
            'state': state_update,
            'timestamp': datetime.now().isoformat()
        })

        # 更新当前状态
        char_data['current_state'].update(state_update)
        char_data['current_state']['last_updated_chapter'] = chapter

        self.save()

    def get_character_state(self, char_id: str,
                            as_of_chapter: int = None) -> Dict:
        """
        获取人物状态

        Args:
            char_id: 人物ID
            as_of_chapter: 截止到某章（用于回溯）

        Returns:
            人物状态
        """
        if char_id not in self.memory['characters']:
            return {}

        char_data = self.memory['characters'][char_id]

        if as_of_chapter is None:
            return char_data['current_state']

        # 回溯到指定章节的状态
        state = {}
        for record in char_data['history']:
            if record['chapter'] <= as_of_chapter:
                state.update(record['state'])
            else:
                break

        return state

    def get_character_history(self, char_id: str) -> List[Dict]:
        """获取人物完整历史"""
        return self.memory['characters'].get(char_id, {}).get('history', [])

    # ========== 时间线追踪 ==========

    def add_timeline_event(self, chapter: int, event: Dict):
        """
        添加时间线事件

        Args:
            chapter: 章节号
            event: 事件信息 {time, description, location, characters}
        """
        timeline_entry = {
            'chapter': chapter,
            'story_time': event.get('time', '未知'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'characters': event.get('characters', []),
            'recorded_at': datetime.now().isoformat()
        }

        self.memory['timeline'].append(timeline_entry)
        self.memory['timeline'].sort(key=lambda x: x['chapter'])
        self.save()

    def get_timeline(self, start_chapter: int = None,
                     end_chapter: int = None) -> List[Dict]:
        """获取时间线"""
        timeline = self.memory['timeline']

        if start_chapter is not None:
            timeline = [e for e in timeline if e['chapter'] >= start_chapter]
        if end_chapter is not None:
            timeline = [e for e in timeline if e['chapter'] <= end_chapter]

        return timeline

    # ========== 伏笔追踪 ==========

    def plant_foreshadowing(self, chapter: int, foreshadow_id: str,
                            description: str, planned_resolve: int = None):
        """
        记录埋设伏笔

        Args:
            chapter: 埋设章节
            foreshadow_id: 伏笔ID
            description: 伏笔描述
            planned_resolve: 计划回收章节
        """
        entry = {
            'id': foreshadow_id,
            'planted_chapter': chapter,
            'description': description,
            'planned_resolve_chapter': planned_resolve,
            'resolved': False,
            'resolved_chapter': None
        }

        # 检查是否已存在
        existing = next((f for f in self.memory['foreshadowing']['planted']
                        if f['id'] == foreshadow_id), None)
        if not existing:
            self.memory['foreshadowing']['planted'].append(entry)
            self.save()

    def resolve_foreshadowing(self, chapter: int, foreshadow_id: str,
                              how_resolved: str = None):
        """
        记录回收伏笔

        Args:
            chapter: 回收章节
            foreshadow_id: 伏笔ID
            how_resolved: 如何回收
        """
        for f in self.memory['foreshadowing']['planted']:
            if f['id'] == foreshadow_id and not f['resolved']:
                f['resolved'] = True
                f['resolved_chapter'] = chapter
                f['how_resolved'] = how_resolved

                self.memory['foreshadowing']['resolved'].append({
                    'id': foreshadow_id,
                    'planted_chapter': f['planted_chapter'],
                    'resolved_chapter': chapter,
                    'how_resolved': how_resolved
                })
                break

        self.save()

    def get_unresolved_foreshadowing(self) -> List[Dict]:
        """获取未回收的伏笔"""
        return [f for f in self.memory['foreshadowing']['planted']
                if not f['resolved']]

    def get_overdue_foreshadowing(self, current_chapter: int,
                                   threshold: int = 50) -> List[Dict]:
        """
        获取超期未回收的伏笔

        Args:
            current_chapter: 当前章节
            threshold: 超过多少章算超期

        Returns:
            超期伏笔列表
        """
        overdue = []
        for f in self.memory['foreshadowing']['planted']:
            if not f['resolved']:
                chapters_passed = current_chapter - f['planted_chapter']
                if chapters_passed > threshold:
                    f['chapters_passed'] = chapters_passed
                    overdue.append(f)
        return overdue

    # ========== 章节摘要索引 ==========

    def add_chapter_summary(self, chapter: int, summary: str,
                            key_events: List[str] = None):
        """
        添加章节摘要

        Args:
            chapter: 章节号
            summary: 摘要内容
            key_events: 关键事件列表
        """
        self.memory['chapter_summaries'][str(chapter)] = {
            'summary': summary,
            'key_events': key_events or [],
            'recorded_at': datetime.now().isoformat()
        }
        self.memory['meta']['total_chapters_tracked'] = len(
            self.memory['chapter_summaries'])
        self.save()

    def get_chapter_summary(self, chapter: int) -> Optional[Dict]:
        """获取章节摘要"""
        return self.memory['chapter_summaries'].get(str(chapter))

    def get_recent_summaries(self, count: int = 5) -> List[Dict]:
        """获取最近的章节摘要"""
        summaries = []
        for ch_str, data in sorted(self.memory['chapter_summaries'].items(),
                                   key=lambda x: int(x[0]), reverse=True):
            summaries.append({
                'chapter': int(ch_str),
                **data
            })
            if len(summaries) >= count:
                break
        return summaries

    # ========== 不一致记录 ==========

    def record_inconsistency(self, chapter: int, issue_type: str,
                             description: str, details: Dict = None):
        """
        记录发现的不一致

        Args:
            chapter: 发现章节
            issue_type: 问题类型
            description: 问题描述
            details: 详细信息
        """
        entry = {
            'chapter': chapter,
            'type': issue_type,
            'description': description,
            'details': details or {},
            'found_at': datetime.now().isoformat(),
            'resolved': False
        }

        self.memory['inconsistencies'].append(entry)
        self.save()

    def get_inconsistencies(self, unresolved_only: bool = True) -> List[Dict]:
        """获取不一致记录"""
        issues = self.memory['inconsistencies']
        if unresolved_only:
            issues = [i for i in issues if not i['resolved']]
        return issues

    def resolve_inconsistency(self, index: int, how_resolved: str):
        """标记不一致为已解决"""
        if 0 <= index < len(self.memory['inconsistencies']):
            self.memory['inconsistencies'][index]['resolved'] = True
            self.memory['inconsistencies'][index]['how_resolved'] = how_resolved
            self.memory['inconsistencies'][index]['resolved_at'] = \
                datetime.now().isoformat()
            self.save()

    # ========== 一致性检查 ==========

    def check_consistency(self, chapter: int, proposed_state: Dict) -> Dict:
        """
        检查提议的状态更新是否与历史一致

        Args:
            chapter: 当前章节
            proposed_state: 提议的状态更新

        Returns:
            检查结果 {consistent: bool, issues: []}
        """
        issues = []

        # 检查人物状态一致性
        for char_id, new_state in proposed_state.get('characters', {}).items():
            current = self.get_character_state(char_id)

            # 检查位置一致性
            if 'location' in new_state and 'location' in current:
                if new_state['location'] != current['location']:
                    # 可能的位置跳跃
                    issues.append({
                        'type': 'character_location',
                        'character': char_id,
                        'description': f"人物位置可能跳跃: {current['location']} -> {new_state['location']}",
                        'severity': 'warning'
                    })

            # 检查能力一致性
            if 'abilities' in new_state and 'abilities' in current:
                lost_abilities = set(current['abilities']) - set(new_state['abilities'])
                if lost_abilities:
                    issues.append({
                        'type': 'character_ability',
                        'character': char_id,
                        'description': f"人物可能丢失能力: {lost_abilities}",
                        'severity': 'warning'
                    })

        return {
            'consistent': len([i for i in issues if i['severity'] == 'critical']) == 0,
            'issues': issues
        }

    # ========== 导出/导入 ==========

    def export_memory(self) -> str:
        """导出记忆库为JSON字符串"""
        return json.dumps(self.memory, ensure_ascii=False, indent=2)

    def import_memory(self, json_str: str):
        """从JSON字符串导入记忆库"""
        self.memory = json.loads(json_str)
        self.save()

    def get_memory_stats(self) -> Dict:
        """获取记忆库统计信息"""
        return {
            'total_chapters_tracked': self.memory['meta']['total_chapters_tracked'],
            'characters_tracked': len(self.memory['characters']),
            'timeline_events': len(self.memory['timeline']),
            'foreshadowing_planted': len(self.memory['foreshadowing']['planted']),
            'foreshadowing_resolved': len(self.memory['foreshadowing']['resolved']),
            'unresolved_foreshadowing': len(self.get_unresolved_foreshadowing()),
            'inconsistencies_found': len(self.memory['inconsistencies']),
            'unresolved_inconsistencies': len(self.get_inconsistencies())
        }
