"""
一致性检查工具模块
"""

import re
from typing import Dict, List, Optional, Any
from pathlib import Path


class ConsistencyChecker:
    """一致性检查器，检查小说中的设定一致性"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    def check_character_name(self, text: str, characters: Dict) -> List[Dict]:
        """检查人物名称一致性"""
        issues = []

        # 收集所有人物名称和别名
        all_names = {}
        for char_type in ['protagonists', 'antagonists', 'supporting']:
            for char in characters.get(char_type, []):
                name = char.get('name', '')
                char_id = char.get('id', '')
                all_names[name] = char_id

                # 检查别名
                for alias in char.get('aliases', []):
                    all_names[alias] = char_id

        # TODO: 实现更复杂的名称一致性检查
        # 例如检测未定义的角色名称出现

        return issues

    def check_timeline(self, chapter_content: str, outline: Dict) -> List[Dict]:
        """检查时间线一致性"""
        issues = []

        # 检查章节大纲中的事件是否在正文中体现
        # 这是一个简化版本，实际需要更复杂的NLP处理

        return issues

    def check_world_rules(self, text: str, world_rules: Dict) -> List[Dict]:
        """检查世界观规则一致性"""
        issues = []

        # 检查科技体系规则
        tech_system = world_rules.get('tech_system', {})
        if tech_system:
            for rule in tech_system.get('tech_rules', []):
                # 检查是否违反规则
                # 简化实现：实际需要语义理解
                pass

        # 检查魔法体系规则
        magic_system = world_rules.get('magic_system', {})
        if magic_system:
            for limit in magic_system.get('costs_and_limits', []):
                pass

        return issues

    def check_terminology(self, text: str, terminology: List[Dict]) -> List[Dict]:
        """检查专有名词使用"""
        issues = []

        for term in terminology:
            term_name = term.get('term', '')
            usage_notes = term.get('usage_notes', '')

            # 检查术语是否在文本中出现
            if term_name in text:
                # 可以添加更复杂的检查逻辑
                pass

        return issues

    def check_foreshadowing(self, chapter_num: int, outline: Dict, text: str) -> List[Dict]:
        """检查伏笔处理"""
        issues = []

        # 获取当前章节的大纲
        chapter_outline = None
        for ch in outline.get('chapters', []):
            if ch.get('number') == chapter_num:
                chapter_outline = ch
                break

        if not chapter_outline:
            return issues

        # 检查应埋下的伏笔
        foreshadowing = chapter_outline.get('foreshadowing', {})
        to_plant = foreshadowing.get('planted', [])

        for item in to_plant:
            # 简化检查：检查关键词是否出现
            if item.get('item') and item['item'] not in text:
                issues.append({
                    'type': 'missing_foreshadowing',
                    'severity': 'warning',
                    'message': f"缺少应埋下的伏笔：{item['item']}",
                    'item': item
                })

        return issues

    def check_pov_consistency(self, text: str, pov_character: str, characters: Dict) -> List[Dict]:
        """检查视角一致性"""
        issues = []

        # 获取POV角色的信息
        pov_char = None
        for char_type in ['protagonists', 'antagonists', 'supporting']:
            for char in characters.get(char_type, []):
                if char.get('id') == pov_character or char.get('name') == pov_character:
                    pov_char = char
                    break

        if not pov_char:
            return issues

        # 检查是否出现了POV角色不应该知道的信息
        # 这需要更复杂的NLP处理，这里简化实现

        return issues

    def full_check(self,
                   chapter_content: str,
                   chapter_num: int,
                   blueprint: Dict,
                   characters: Dict,
                   outline: Dict,
                   world_rules: Dict) -> Dict:
        """
        执行完整的一致性检查
        返回: {
            'passed': bool,
            'issues': [...],
            'summary': str
        }
        """
        all_issues = []

        # 执行各项检查
        all_issues.extend(self.check_character_name(chapter_content, characters))
        all_issues.extend(self.check_timeline(chapter_content, outline))
        all_issues.extend(self.check_world_rules(chapter_content, world_rules))
        all_issues.extend(self.check_terminology(chapter_content, world_rules.get('terminology', [])))
        all_issues.extend(self.check_foreshadowing(chapter_num, outline, chapter_content))

        # 获取当前章节的POV角色
        chapter_outline = None
        for ch in outline.get('chapters', []):
            if ch.get('number') == chapter_num:
                chapter_outline = ch
                break

        if chapter_outline:
            pov_char = chapter_outline.get('pov_character', '')
            all_issues.extend(self.check_pov_consistency(chapter_content, pov_char, characters))

        # 统计问题严重程度
        critical = sum(1 for i in all_issues if i.get('severity') == 'critical')
        warnings = sum(1 for i in all_issues if i.get('severity') == 'warning')

        passed = critical == 0

        summary = f"检查完成: {len(all_issues)}个问题"
        if critical > 0:
            summary += f" (严重: {critical})"
        if warnings > 0:
            summary += f" (警告: {warnings})"

        return {
            'passed': passed,
            'issues': all_issues,
            'critical_count': critical,
            'warning_count': warnings,
            'summary': summary
        }
