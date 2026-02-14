"""
跨章节一致性检查模块

核心功能：在关键节点进行全局一致性检查
解决痛点：长篇小说在后期容易出现与前期的矛盾
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from utils.api_client import get_client
from utils.file_manager import FileManager
from core.memory_store import MemoryStore


class ConsistencyChecker:
    """
    跨章节一致性检查器

    检查维度：
    1. 人物状态一致性（位置、关系、能力）
    2. 时间线一致性
    3. 伏笔完整性
    4. 世界规则一致性
    5. 剧情连贯性
    """

    # 检查触发点
    CHECKPOINTS = {
        'per_chapter': 1,      # 每章简单检查
        'minor': 10,           # 每10章小检查
        'major': 50,           # 每50章大检查
        'volume_end': None,    # 每卷结束检查
        'final': None          # 完本检查
    }

    def __init__(self, project_path: str, config: Dict = None):
        self.project_path = Path(project_path)
        self.config = config or {}
        self.api_config = self.config.get('api', {})
        self.file_manager = FileManager(project_path)
        self.memory_store = MemoryStore(project_path)

    def should_check(self, chapter_num: int, check_type: str) -> bool:
        """判断是否应该进行检查"""
        checkpoint = self.CHECKPOINTS.get(check_type)
        if checkpoint is None:
            return False
        return chapter_num % checkpoint == 0

    def run_checkpoint_check(self, chapter_num: int) -> Dict:
        """
        运行检查点检查

        自动判断检查级别并执行
        """
        if chapter_num % 50 == 0:
            return self.major_check(chapter_num)
        elif chapter_num % 10 == 0:
            return self.minor_check(chapter_num)
        else:
            return self.per_chapter_check(chapter_num)

    def per_chapter_check(self, chapter_num: int) -> Dict:
        """
        每章简单检查

        检查内容：
        - 与前一章的连贯性
        - 基本人物状态
        """
        issues = []

        # 获取当前章节和前一章
        current_chapter = self._get_chapter_content(chapter_num)
        prev_chapter = self._get_chapter_content(chapter_num - 1) if chapter_num > 1 else None

        if prev_chapter:
            # 检查与前章的连贯性
            continuity_issues = self._check_continuity(
                prev_chapter, current_chapter, chapter_num
            )
            issues.extend(continuity_issues)

        # 检查人物状态
        char_issues = self._check_character_states(chapter_num, current_chapter)
        issues.extend(char_issues)

        return {
            'check_type': 'per_chapter',
            'chapter': chapter_num,
            'passed': len([i for i in issues if i['severity'] == 'critical']) == 0,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }

    def minor_check(self, chapter_num: int) -> Dict:
        """
        小检查（每10章）

        检查内容：
        - 最近10章的连贯性
        - 伏笔状态
        - 人物发展弧线
        """
        issues = []

        # 检查最近章节连贯性
        recent_issues = self._check_recent_chapters(chapter_num, 10)
        issues.extend(recent_issues)

        # 检查伏笔
        foreshadow_issues = self._check_foreshadowing_status(chapter_num)
        issues.extend(foreshadow_issues)

        # 检查人物弧线
        arc_issues = self._check_character_arcs(chapter_num)
        issues.extend(arc_issues)

        return {
            'check_type': 'minor',
            'chapter': chapter_num,
            'passed': len([i for i in issues if i['severity'] == 'critical']) == 0,
            'issues': issues,
            'stats': self.memory_store.get_memory_stats(),
            'timestamp': datetime.now().isoformat()
        }

    def major_check(self, chapter_num: int) -> Dict:
        """
        大检查（每50章）

        检查内容：
        - 全局一致性
        - 所有未回收伏笔
        - 时间线完整性
        - AI深度分析
        """
        issues = []

        # 全局一致性检查
        global_issues = self._check_global_consistency(chapter_num)
        issues.extend(global_issues)

        # 伏笔完整性
        foreshadow_issues = self._check_all_foreshadowing(chapter_num)
        issues.extend(foreshadow_issues)

        # 时间线检查
        timeline_issues = self._check_timeline_consistency(chapter_num)
        issues.extend(timeline_issues)

        # AI深度分析（可选）
        ai_issues = self._ai_deep_analysis(chapter_num)
        issues.extend(ai_issues)

        return {
            'check_type': 'major',
            'chapter': chapter_num,
            'passed': len([i for i in issues if i['severity'] == 'critical']) == 0,
            'issues': issues,
            'stats': self.memory_store.get_memory_stats(),
            'recommendations': self._generate_recommendations(issues),
            'timestamp': datetime.now().isoformat()
        }

    def volume_check(self, volume_num: int, chapter_range: Tuple[int, int]) -> Dict:
        """
        卷末检查

        Args:
            volume_num: 卷号
            chapter_range: 章节范围 (start, end)
        """
        start_ch, end_ch = chapter_range
        issues = []

        # 检查本卷所有章节
        for ch in range(start_ch, end_ch + 1):
            ch_issues = self._check_chapter_in_volume(ch, volume_num)
            issues.extend(ch_issues)

        # 检查本卷伏笔回收
        volume_foreshadow_issues = self._check_volume_foreshadowing(
            volume_num, chapter_range
        )
        issues.extend(volume_foreshadow_issues)

        return {
            'check_type': 'volume_end',
            'volume': volume_num,
            'chapter_range': chapter_range,
            'passed': len([i for i in issues if i['severity'] == 'critical']) == 0,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }

    # ========== 内部检查方法 ==========

    def _get_chapter_content(self, chapter_num: int) -> Optional[str]:
        """获取章节内容"""
        files = self.file_manager.list_files('chapters',
                                              f'chapter_{chapter_num:03d}*.md')
        if files:
            return self.file_manager.read_markdown(files[0])
        return None

    def _check_continuity(self, prev_content: str, curr_content: str,
                          chapter_num: int) -> List[Dict]:
        """检查章节间连贯性"""
        issues = []

        # 获取前一章末尾信息
        prev_ending = prev_content[-500:] if prev_content else ""

        # 获取当前章开头
        curr_beginning = curr_content[:500] if curr_content else ""

        # 使用AI检查连贯性（简化版本可用规则）
        if self.api_config.get('api_key') or self.api_config.get('enabled'):
            try:
                continuity_issues = self._ai_check_continuity(
                    prev_ending, curr_beginning, chapter_num
                )
                issues.extend(continuity_issues)
            except Exception as e:
                # AI检查失败，记录但不中断
                issues.append({
                    'type': 'continuity',
                    'severity': 'warning',
                    'description': f'连贯性检查失败: {str(e)}',
                    'chapter': chapter_num
                })

        return issues

    def _ai_check_continuity(self, prev_ending: str, curr_beginning: str,
                              chapter_num: int) -> List[Dict]:
        """使用AI检查连贯性"""
        prompt = f"""检查以下两段文字的连贯性。

## 前一章结尾
{prev_ending}

## 当前章开头
{curr_beginning}

## 检查要点
1. 场景是否自然过渡
2. 时间是否连续
3. 人物位置是否合理
4. 是否有明显的断裂感

## 输出格式
```json
{{
  "coherent": true/false,
  "issues": [
    {{
      "type": "问题类型",
      "description": "问题描述",
      "severity": "critical/warning/suggestion"
    }}
  ]
}}
```"""

        try:
            client = get_client(self.api_config)
            response = client.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )

            # 解析响应
            response = response.strip()
            if response.startswith('```'):
                response = response.split('\n', 1)[1]
            if response.endswith('```'):
                response = response.rsplit('```', 1)[0]

            result = json.loads(response.strip())

            issues = []
            for issue in result.get('issues', []):
                issue['chapter'] = chapter_num
                issues.append(issue)

            return issues

        except Exception:
            return []

    def _check_character_states(self, chapter_num: int,
                                 content: str) -> List[Dict]:
        """检查人物状态一致性"""
        issues = []

        # 从记忆库获取人物当前状态
        memory_stats = self.memory_store.get_memory_stats()

        # 检查是否有超期未更新的人物
        for char_id, char_data in self.memory_store.memory.get('characters', {}).items():
            last_updated = char_data.get('current_state', {}).get('last_updated_chapter', 0)
            if chapter_num - last_updated > 20:
                issues.append({
                    'type': 'character_state',
                    'severity': 'warning',
                    'description': f'人物 {char_id} 已超过20章未更新状态',
                    'chapter': chapter_num,
                    'character': char_id
                })

        return issues

    def _check_recent_chapters(self, chapter_num: int,
                                lookback: int) -> List[Dict]:
        """检查最近章节的一致性"""
        issues = []

        start_ch = max(1, chapter_num - lookback)

        # 获取这段时间的章节摘要
        summaries = []
        for ch in range(start_ch, chapter_num + 1):
            summary = self.memory_store.get_chapter_summary(ch)
            if summary:
                summaries.append({
                    'chapter': ch,
                    'summary': summary.get('summary', ''),
                    'events': summary.get('key_events', [])
                })

        # 检查时间线跳跃
        if len(summaries) >= 2:
            # 简单检查：相邻章节的事件是否有明显跳跃
            for i in range(1, len(summaries)):
                prev = summaries[i - 1]
                curr = summaries[i]
                # 这里可以添加更复杂的时间线检查逻辑

        return issues

    def _check_foreshadowing_status(self, chapter_num: int) -> List[Dict]:
        """检查伏笔状态"""
        issues = []

        # 获取超期未回收的伏笔
        overdue = self.memory_store.get_overdue_foreshadowing(
            chapter_num, threshold=30
        )

        for f in overdue:
            issues.append({
                'type': 'foreshadowing',
                'severity': 'warning',
                'description': f"伏笔 '{f['id']}' 已超过 {f['chapters_passed']} 章未回收",
                'chapter': chapter_num,
                'foreshadow_id': f['id'],
                'planted_chapter': f['planted_chapter']
            })

        return issues

    def _check_character_arcs(self, chapter_num: int) -> List[Dict]:
        """检查人物发展弧线"""
        issues = []

        # TODO: 实现人物弧线检查
        # 检查人物是否有成长/变化
        # 检查人物目标是否还在追踪

        return issues

    def _check_global_consistency(self, chapter_num: int) -> List[Dict]:
        """检查全局一致性"""
        issues = []

        # 检查记忆库中的不一致记录
        inconsistencies = self.memory_store.get_inconsistencies(unresolved_only=True)

        for inc in inconsistencies:
            issues.append({
                'type': 'global_inconsistency',
                'severity': 'critical',
                'description': inc.get('description', ''),
                'chapter': chapter_num,
                'original_chapter': inc.get('chapter'),
                'details': inc.get('details', {})
            })

        return issues

    def _check_all_foreshadowing(self, chapter_num: int) -> List[Dict]:
        """检查所有伏笔状态"""
        issues = []

        # 获取所有未回收的伏笔
        unresolved = self.memory_store.get_unresolved_foreshadowing()

        for f in unresolved:
            chapters_passed = chapter_num - f['planted_chapter']

            if chapters_passed > 50:
                severity = 'critical'
            elif chapters_passed > 30:
                severity = 'warning'
            else:
                severity = 'suggestion'

            issues.append({
                'type': 'foreshadowing',
                'severity': severity,
                'description': f"伏笔 '{f['id']}' 已 {chapters_passed} 章未回收",
                'chapter': chapter_num,
                'foreshadow_id': f['id'],
                'planted_chapter': f['planted_chapter'],
                'description_detail': f.get('description', '')
            })

        return issues

    def _check_timeline_consistency(self, chapter_num: int) -> List[Dict]:
        """检查时间线一致性"""
        issues = []

        timeline = self.memory_store.get_timeline()

        # 检查时间线是否有明显问题
        prev_time = None
        for event in timeline:
            current_time = event.get('story_time')
            if prev_time and current_time:
                # 这里可以添加更复杂的时间线检查
                pass
            prev_time = current_time

        return issues

    def _check_chapter_in_volume(self, chapter_num: int,
                                  volume_num: int) -> List[Dict]:
        """检查卷内章节"""
        # 简化实现
        return []

    def _check_volume_foreshadowing(self, volume_num: int,
                                     chapter_range: Tuple[int, int]) -> List[Dict]:
        """检查卷内伏笔"""
        issues = []
        start_ch, end_ch = chapter_range

        # 检查本卷应该回收的伏笔是否已回收
        for f in self.memory_store.memory.get('foreshadowing', {}).get('planted', []):
            planned_resolve = f.get('planned_resolve_chapter')
            if planned_resolve and start_ch <= planned_resolve <= end_ch:
                if not f.get('resolved'):
                    issues.append({
                        'type': 'foreshadowing',
                        'severity': 'warning',
                        'description': f"伏笔 '{f['id']}' 计划在本卷回收但未完成",
                        'volume': volume_num,
                        'foreshadow_id': f['id']
                    })

        return issues

    def _ai_deep_analysis(self, chapter_num: int) -> List[Dict]:
        """AI深度分析（用于大检查点）"""
        if not (self.api_config.get('api_key') or self.api_config.get('enabled')):
            return []

        # 获取最近章节摘要
        summaries = self.memory_store.get_recent_summaries(10)
        summary_text = '\n'.join([
            f"第{s['chapter']}章: {s['summary']}"
            for s in summaries
        ])

        # 获取伏笔状态
        unresolved = self.memory_store.get_unresolved_foreshadowing()
        foreshadow_text = '\n'.join([
            f"- {f['id']}: 埋设于第{f['planted_chapter']}章"
            for f in unresolved[:10]
        ])

        prompt = f"""请分析以下小说的整体一致性。

## 最近章节摘要
{summary_text}

## 未回收伏笔
{foreshadow_text if foreshadow_text else '无'}

## 检查要点
1. 剧情发展是否连贯
2. 是否有明显的逻辑漏洞
3. 伏笔是否有被遗忘的风险
4. 人物发展是否合理

## 输出格式
```json
{{
  "analysis": "整体分析",
  "potential_issues": [
    {{
      "type": "问题类型",
      "description": "问题描述",
      "severity": "critical/warning/suggestion",
      "suggestion": "建议"
    }}
  ]
}}
```"""

        try:
            client = get_client(self.api_config)
            response = client.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.3
            )

            response = response.strip()
            if response.startswith('```'):
                response = response.split('\n', 1)[1]
            if response.endswith('```'):
                response = response.rsplit('```', 1)[0]

            result = json.loads(response.strip())

            issues = []
            for issue in result.get('potential_issues', []):
                issue['chapter'] = chapter_num
                issue['source'] = 'ai_deep_analysis'
                issues.append(issue)

            return issues

        except Exception:
            return []

    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """根据问题生成建议"""
        recommendations = []

        critical_count = len([i for i in issues if i['severity'] == 'critical'])
        warning_count = len([i for i in issues if i['severity'] == 'warning'])

        if critical_count > 0:
            recommendations.append(f"发现 {critical_count} 个严重问题，建议立即修复")

        if warning_count > 5:
            recommendations.append(f"发现 {warning_count} 个警告，建议在后续章节中逐步解决")

        # 针对特定类型问题的建议
        foreshadow_issues = [i for i in issues if i['type'] == 'foreshadowing']
        if len(foreshadow_issues) > 3:
            recommendations.append("伏笔积压较多，建议在接下来的10章内集中回收部分伏笔")

        return recommendations
