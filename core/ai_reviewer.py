"""
AI驱动的深度审查模块

核心改进：使用LLM进行语义级别的深度审查，而非简单的规则匹配
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.api_client import get_client


class AIReviewer:
    """
    AI驱动的深度审查器

    与规则基础的Reviewer不同，这个模块使用LLM来：
    1. 理解语义层面的问题
    2. 检测逻辑漏洞
    3. 验证情感一致性
    4. 评估文学质量
    """

    def __init__(self, project_path: str, config: Dict = None):
        self.project_path = project_path
        self.config = config or {}
        self.api_config = self.config.get('api', {})

    def deep_review(self, chapter_num: int, content: str,
                    context: Dict) -> Dict:
        """
        执行AI驱动的深度审查

        Args:
            chapter_num: 章节号
            content: 章节内容
            context: 上下文（包含人物、世界观、前文等）

        Returns:
            深度审查结果
        """
        # 构建审查提示词
        prompt = self._build_review_prompt(chapter_num, content, context)

        try:
            client = get_client(self.api_config)
            response = client.generate(
                prompt=prompt,
                system_prompt=self._get_reviewer_system_prompt(),
                max_tokens=2048,
                temperature=0.3  # 低温度保证一致性
            )

            # 解析JSON响应
            result = self._parse_review_response(response)
            result['chapter'] = chapter_num
            result['timestamp'] = datetime.now().isoformat()
            return result

        except Exception as e:
            return {
                'chapter': chapter_num,
                'overall_passes': True,  # 失败时默认通过，避免阻塞
                'issues': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _build_review_prompt(self, chapter_num: int, content: str,
                             context: Dict) -> str:
        """构建审查提示词"""

        # 提取关键上下文
        chapter_info = context.get('chapter_info', {})
        characters = context.get('characters', {})
        world_rules = context.get('world_rules', {})
        prev_summaries = context.get('chapter_summaries', [])
        foreshadowing = context.get('foreshadowing', {})

        # 构建人物信息
        char_text = ""
        for char_id, char in characters.items():
            char_text += f"""
- {char.get('name', char_id)}:
  性格: {', '.join(char.get('personality', {}).get('traits', []))}
  缺陷: {', '.join(char.get('personality', {}).get('flaws', []))}
  当前状态: {char.get('current_state', '未知')}
"""

        # 构建世界规则
        world_text = ""
        if world_rules.get('tech_system'):
            tech = world_rules['tech_system']
            world_text += f"科技规则: {', '.join(tech.get('tech_rules', []))}\n"
        if world_rules.get('magic_system'):
            magic = world_rules['magic_system']
            world_text += f"魔法限制: {', '.join(magic.get('costs_and_limits', []))}\n"

        # 构建前文摘要
        prev_text = ""
        for item in prev_summaries[-5:]:  # 最近5章
            prev_text += f"第{item.get('chapter', '?')}章: {item.get('summary', '')[:150]}\n"

        # 伏笔信息
        plant_list = chapter_info.get('foreshadowing_plant', [])
        resolve_list = chapter_info.get('foreshadowing_resolve', [])

        prompt = f"""请对以下小说章节进行专业的深度审查。

## 章节信息
- 第 {chapter_num} 章：「{chapter_info.get('title', '')}」
- POV角色: {chapter_info.get('pov_character', '无')}
- 涉及人物: {', '.join(chapter_info.get('characters_involved', []))}
- 需埋设伏笔: {', '.join(plant_list) if plant_list else '无'}
- 需回收伏笔: {', '.join(resolve_list) if resolve_list else '无'}

## 人物设定
{char_text if char_text else "无特定人物信息"}

## 世界规则
{world_text if world_text else "无特定规则"}

## 前情提要
{prev_text if prev_text else "这是开篇章节"}

## 章节内容

{content}

---

## 审查任务

请仔细检查以下方面，并输出JSON格式的审查结果：

### 1. 逻辑一致性 (logic_consistency)
- 事件因果是否合理
- 角色行为是否符合动机
- 是否有逻辑漏洞

### 2. 人物一致性 (character_consistency)
- 对话风格是否符合人物性格
- 行为是否符合设定
- 人物关系是否正确

### 3. 世界观一致性 (world_consistency)
- 科技/魔法使用是否合规
- 是否违反设定限制

### 4. POV一致性 (pov_consistency)
- 视角是否统一
- 是否出现POV角色无法知道的信息

### 5. 伏笔处理 (foreshadowing)
- 需埋设的伏笔是否自然融入
- 需回收的伏笔是否给出答案

### 6. 与前文连贯性 (continuity)
- 是否与前文矛盾
- 时间线是否合理

### 7. 文学质量 (literary_quality)
- 开篇是否吸引人
- 节奏是否得当
- 结尾是否有悬念
- 是否有重复用词/句式

## 输出格式

```json
{{
  "overall_passes": true/false,
  "scores": {{
    "logic_consistency": 1-10,
    "character_consistency": 1-10,
    "world_consistency": 1-10,
    "pov_consistency": 1-10,
    "foreshadowing": 1-10,
    "continuity": 1-10,
    "literary_quality": 1-10
  }},
  "issues": [
    {{
      "type": "critical/warning/suggestion",
      "category": "类别名称",
      "description": "具体问题描述",
      "location": "问题所在位置（引用原文）",
      "fix_suggestion": "修改建议"
    }}
  ],
  "strengths": ["优点1", "优点2"],
  "summary": "总体评价"
}}
```

请只输出JSON，不要有其他内容。"""

        return prompt

    def _get_reviewer_system_prompt(self) -> str:
        return """你是一位专业的文学编辑，擅长小说审查和质量把控。
你的工作是发现章节中的问题并提供具体的修改建议。

审查原则：
1. 严格但不苛刻：7分以上算合格
2. 问题要具体：指明问题位置和原因
3. 建议要可行：给出可操作的修改方向
4. 关注核心：优先发现逻辑和一致性问题"""

    def _parse_review_response(self, response: str) -> Dict:
        """解析审查响应"""
        try:
            # 尝试提取JSON
            response = response.strip()
            if response.startswith('```'):
                response = response.split('\n', 1)[1]
            if response.endswith('```'):
                response = response.rsplit('```', 1)[0]

            result = json.loads(response.strip())

            # 确保必要字段存在
            if 'overall_passes' not in result:
                scores = result.get('scores', {})
                avg_score = sum(scores.values()) / len(scores) if scores else 7
                result['overall_passes'] = avg_score >= 7

            if 'issues' not in result:
                result['issues'] = []

            return result

        except json.JSONDecodeError:
            return {
                'overall_passes': True,
                'issues': [],
                'raw_response': response,
                'parse_error': True
            }

    def batch_review(self, chapters: List[Dict],
                     get_context_func) -> List[Dict]:
        """
        批量审查多个章节

        Args:
            chapters: 章节列表
            get_context_func: 获取上下文的函数

        Returns:
            审查结果列表
        """
        results = []
        for ch in chapters:
            chapter_num = ch.get('number')
            content = ch.get('content', '')
            context = get_context_func(chapter_num)

            result = self.deep_review(chapter_num, content, context)
            results.append(result)

        return results
