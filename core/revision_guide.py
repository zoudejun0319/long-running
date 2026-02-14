"""
智能修订指导模块

核心功能：不只是告诉AI"有问题"，而是指导它"怎么改"
解决痛点：传统审查只输出问题列表，AI修订时不知具体方向
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.api_client import get_client


class RevisionGuide:
    """
    智能修订指导器

    功能：
    1. 分析审查结果，生成具体修订指导
    2. 提供可操作的修改建议
    3. 生成修订提示词
    """

    def __init__(self, project_path: str, config: Dict = None):
        self.project_path = project_path
        self.config = config or {}
        self.api_config = self.config.get('api', {})

    def generate_revision_guide(self, original_content: str,
                                 review_result: Dict,
                                 context: Dict) -> Dict:
        """
        生成修订指导

        Args:
            original_content: 原始章节内容
            review_result: 审查结果
            context: 上下文

        Returns:
            修订指导 {guide: str, priority_issues: [], prompt: str}
        """
        issues = review_result.get('issues', [])

        if not issues:
            return {
                'needs_revision': False,
                'guide': '无需修订',
                'priority_issues': [],
                'prompt': None
            }

        # 分类和排序问题
        prioritized = self._prioritize_issues(issues)

        # 生成修订指导
        guide = self._create_revision_guide(prioritized, context)

        # 生成修订提示词
        prompt = self._create_revision_prompt(
            original_content, prioritized, guide, context
        )

        return {
            'needs_revision': True,
            'guide': guide,
            'priority_issues': prioritized,
            'prompt': prompt
        }

    def _prioritize_issues(self, issues: List[Dict]) -> List[Dict]:
        """
        问题优先级排序

        优先级：critical > warning > suggestion
        同级别按类别排序：logic > character > world > pov > literary
        """
        severity_order = {'critical': 0, 'warning': 1, 'suggestion': 2}
        category_order = {
            'logic_consistency': 0,
            'character_consistency': 1,
            'world_consistency': 2,
            'pov_consistency': 3,
            'continuity': 4,
            'foreshadowing': 5,
            'literary_quality': 6
        }

        def sort_key(issue):
            severity = severity_order.get(issue.get('type', 'suggestion'), 2)
            category = category_order.get(issue.get('category', ''), 10)
            return (severity, category)

        return sorted(issues, key=sort_key)

    def _create_revision_guide(self, issues: List[Dict],
                                context: Dict) -> str:
        """创建修订指导文档"""
        guide_parts = ["# 修订指导\n"]

        # 按类别分组
        by_category = {}
        for issue in issues:
            cat = issue.get('category', 'other')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(issue)

        category_names = {
            'logic_consistency': '逻辑一致性',
            'character_consistency': '人物一致性',
            'world_consistency': '世界观一致性',
            'pov_consistency': '视角一致性',
            'continuity': '连贯性',
            'foreshadowing': '伏笔处理',
            'literary_quality': '文学质量'
        }

        for cat, cat_issues in by_category.items():
            cat_name = category_names.get(cat, cat)
            guide_parts.append(f"\n## {cat_name}\n")

            for i, issue in enumerate(cat_issues, 1):
                severity = issue.get('type', 'warning')
                severity_mark = {'critical': '❗', 'warning': '⚠️', 'suggestion': '💡'}
                mark = severity_mark.get(severity, '•')

                guide_parts.append(f"\n{mark} **问题 {i}** ({severity})")
                guide_parts.append(f"\n   - 位置: {issue.get('location', '未指定')}")
                guide_parts.append(f"\n   - 问题: {issue.get('description', '')}")

                fix = issue.get('fix_suggestion', '')
                if fix:
                    guide_parts.append(f"\n   - 修改建议: {fix}")

                guide_parts.append("\n")

        return ''.join(guide_parts)

    def _create_revision_prompt(self, original_content: str,
                                 issues: List[Dict],
                                 guide: str,
                                 context: Dict) -> str:
        """创建修订提示词"""

        chapter_info = context.get('chapter_info', {})

        # 提取关键上下文
        context_text = self._build_context_text(context)

        # 构建问题摘要
        critical_issues = [i for i in issues if i.get('type') == 'critical']
        warning_issues = [i for i in issues if i.get('type') == 'warning']

        prompt = f"""你需要修订以下小说章节。

## 章节信息
- 第 {context.get('chapter_num', '?')} 章：「{chapter_info.get('title', '')}」
- 字数要求: 2500-5000字

## 上下文参考

{context_text}

## 原始内容

{original_content[:4000]}

---

## 需要修复的问题

### 严重问题（必须修复）
{self._format_issues_for_prompt(critical_issues) if critical_issues else '无'}

### 警告问题（建议修复）
{self._format_issues_for_prompt(warning_issues) if warning_issues else '无'}

---

## 修订要求

1. **保持剧情框架**：不要改变核心事件和发展方向
2. **针对性修复**：根据上述问题逐一修改
3. **保持风格一致**：延续原有的写作风格
4. **确保字数达标**：修订后字数仍需在2500-5000之间
5. **保持连贯性**：确保修改不影响与其他章节的衔接

## 特别注意

{self._get_special_instructions(issues, context)}

---

请输出修订后的完整章节内容（不要包含标题）："""

        return prompt

    def _build_context_text(self, context: Dict) -> str:
        """构建上下文文本"""
        parts = []

        # 人物信息
        characters = context.get('characters', {})
        if characters:
            parts.append("### 相关人物")
            for char_id, char in list(characters.items())[:3]:
                parts.append(f"- {char.get('name', char_id)}: {', '.join(char.get('personality', {}).get('traits', [])[:3])}")

        # 世界规则
        world_rules = context.get('world_rules', {})
        if world_rules.get('tech_system'):
            parts.append("\n### 科技规则")
            rules = world_rules['tech_system'].get('tech_rules', [])
            parts.extend([f"- {r}" for r in rules[:3]])
        if world_rules.get('magic_system'):
            parts.append("\n### 魔法限制")
            limits = world_rules['magic_system'].get('costs_and_limits', [])
            parts.extend([f"- {l}" for l in limits[:3]])

        # 前文摘要
        summaries = context.get('chapter_summaries', [])
        if summaries:
            parts.append("\n### 前情提要")
            for item in summaries[-3:]:
                parts.append(f"- 第{item.get('chapter', '?')}章: {item.get('summary', '')[:100]}")

        return '\n'.join(parts) if parts else "无特殊上下文"

    def _format_issues_for_prompt(self, issues: List[Dict]) -> str:
        """格式化问题列表"""
        if not issues:
            return "无"

        lines = []
        for i, issue in enumerate(issues, 1):
            lines.append(f"{i}. [{issue.get('category', '?')}] {issue.get('description', '')}")
            if issue.get('fix_suggestion'):
                lines.append(f"   → 修改建议: {issue['fix_suggestion']}")
            if issue.get('location'):
                lines.append(f"   → 位置: {issue['location'][:100]}")

        return '\n'.join(lines)

    def _get_special_instructions(self, issues: List[Dict],
                                   context: Dict) -> str:
        """获取特殊指令"""
        instructions = []

        # 检查是否有特定类型的问题
        issue_types = {i.get('category') for i in issues}

        if 'character_consistency' in issue_types:
            instructions.append("- 注意人物对话风格和行为必须符合其性格设定")

        if 'world_consistency' in issue_types:
            instructions.append("- 严格遵守世界观规则，不要违反已设定的限制")

        if 'pov_consistency' in issue_types:
            pov_char = context.get('chapter_info', {}).get('pov_character', '')
            instructions.append(f"- 保持{pov_char}的限制视角，不要描写TA无法知道的事情")

        if 'foreshadowing' in issue_types:
            instructions.append("- 确保伏笔自然融入剧情，不要刻意突兀")

        if 'logic_consistency' in issue_types:
            instructions.append("- 检查事件因果关系，确保逻辑通顺")

        return '\n'.join(instructions) if instructions else "请仔细阅读问题列表并针对性修改。"

    def generate_ai_revision(self, original_content: str,
                              review_result: Dict,
                              context: Dict) -> str:
        """
        使用AI生成修订版本

        Args:
            original_content: 原始内容
            review_result: 审查结果
            context: 上下文

        Returns:
            修订后的内容
        """
        guide = self.generate_revision_guide(
            original_content, review_result, context
        )

        if not guide['needs_revision']:
            return original_content

        try:
            client = get_client(self.api_config)

            response = client.generate(
                prompt=guide['prompt'],
                system_prompt=self._get_revision_system_prompt(),
                max_tokens=4096,
                temperature=0.5
            )

            return response

        except Exception as e:
            print(f"AI修订失败: {e}")
            return original_content

    def _get_revision_system_prompt(self) -> str:
        return """你是一位专业的小说编辑，擅长修订和润色文字。

修订原则：
1. 最小改动原则：只修改有问题的部分，不要重写整章
2. 风格一致原则：保持作者原有的写作风格
3. 逻辑优先原则：优先解决逻辑和一致性问题
4. 自然融入原则：修改要自然，不要有明显的"补丁感"

输出要求：
- 直接输出修订后的章节正文
- 不要包含章节标题
- 不要解释修改了什么"""
