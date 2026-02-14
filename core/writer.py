"""
写作代理模块 - 增强版

核心改进：
1. 自动修订循环（质量不通过时自动重写）
2. 批量写作支持
3. 增强的上下文管理
4. 章节摘要生成
5. 【新增】AI深度审查
6. 【新增】全局记忆库集成
7. 【新增】智能修订指导
8. 【新增】跨章节一致性检查
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import time

from utils.file_manager import FileManager
from utils.git_helper import GitHelper
from utils.word_counter import WordCounter
from utils.api_client import get_client
from core.reviewer import Reviewer
# 新增模块
from core.ai_reviewer import AIReviewer
from core.memory_store import MemoryStore
from core.revision_guide import RevisionGuide
from core.consistency_checker import ConsistencyChecker


class Writer:
    """
    写作代理 - 完全自动化

    新增功能：
    1. 自动修订：质量不通过时自动重写（最多3次）
    2. 批量写作：一次写多个章节
    3. 上下文管理：维护章节摘要
    """

    def __init__(self, project_path: str, config: Dict = None):
        self.project_path = Path(project_path)
        self.config = config or {}
        self.api_config = self.config.get('api', {})
        self.file_manager = FileManager(project_path)
        self.git_helper = GitHelper(project_path)
        self.reviewer = Reviewer(project_path, config)

        # 【新增】增强模块初始化
        self.ai_reviewer = AIReviewer(project_path, config)
        self.memory_store = MemoryStore(project_path)
        self.revision_guide = RevisionGuide(project_path, config)
        self.consistency_checker = ConsistencyChecker(project_path, config)

        # 加载项目数据
        self.chapter_list = self.file_manager.read_json('chapter_list.json') or {}
        self.characters = self.file_manager.read_json('characters.json') or {}
        self.foreshadowing = self.file_manager.read_json('foreshadowing.json') or {}
        self.quality_checklist = self.file_manager.read_json('quality_checklist.json') or {}
        self.writing_guide = self.file_manager.read_markdown('writing_guide.md') or ''
        self.world_rules = self._load_world_rules()

        # 自动化配置
        self.max_revisions = 3  # 最大修订次数
        self.retry_delay = 2   # 修订间隔秒数

        # 【新增】质量控制配置
        self.use_ai_review = self.config.get('writing', {}).get('use_ai_review', True)
        self.use_deep_consistency_check = self.config.get('writing', {}).get('use_deep_consistency_check', True)

    def _load_world_rules(self) -> Dict:
        rules = {}
        world_rules_dir = self.project_path / 'world_rules'
        if world_rules_dir.exists():
            for file in world_rules_dir.glob('*.json'):
                key = file.stem
                data = self.file_manager.read_json(f'world_rules/{file.name}')
                if data:
                    rules[key] = data
        return rules

    def run(self, chapter_num: int = None, auto_revise: bool = True) -> Dict:
        """
        运行写作代理（单章）- 增强版

        Args:
            chapter_num: 指定章节号
            auto_revise: 是否自动修订

        Returns:
            写作结果
        """
        if chapter_num is None:
            chapter_num = self._get_next_chapter()

        if chapter_num is None:
            return {'success': False, 'message': '所有章节已完成!'}

        chapter_info = self._get_chapter_info(chapter_num)
        if not chapter_info:
            return {'success': False, 'message': f'找不到第{chapter_num}章信息'}

        # 检查前一章节
        if chapter_num > 1:
            prev_chapter = self._get_chapter_info(chapter_num - 1)
            if prev_chapter and not prev_chapter.get('passes', False):
                print(f"警告: 第{chapter_num - 1}章尚未通过，建议先完成前一章节")

        # 【新增】跨章节一致性检查（检查点）
        if self.use_deep_consistency_check:
            consistency_result = self.consistency_checker.run_checkpoint_check(chapter_num)
            if consistency_result.get('issues'):
                critical = [i for i in consistency_result['issues'] if i['severity'] == 'critical']
                if critical:
                    print(f"警告: 发现 {len(critical)} 个严重一致性问题")
                    for issue in critical[:3]:
                        print(f"  - {issue.get('description', '')}")

        # 收集上下文（包含记忆库信息）
        context = self._build_context(chapter_num, chapter_info)

        # 【新增】从记忆库获取相关信息
        context['memory'] = {
            'unresolved_foreshadowing': self.memory_store.get_unresolved_foreshadowing(),
            'recent_summaries': self.memory_store.get_recent_summaries(5),
            'character_states': {
                char_id: self.memory_store.get_character_state(char_id)
                for char_id in chapter_info.get('characters_involved', [])
            }
        }

        # 生成章节
        print(f"开始创作第 {chapter_num} 章...")
        chapter_content = self._generate_chapter(context)

        # 质量检查（规则基础）
        print("基础质量检查...")
        review_result = self._review_chapter(chapter_num, chapter_content)
        passes = review_result.get('overall_passes', False)

        # 【新增】AI深度审查（可选）
        if self.use_ai_review and passes:
            print("AI深度审查...")
            ai_review = self.ai_reviewer.deep_review(chapter_num, chapter_content, context)
            if not ai_review.get('overall_passes', True):
                passes = False
                review_result['ai_review'] = ai_review
                review_result['issues'].extend(ai_review.get('issues', []))

        # 自动修订（使用智能修订指导）
        revision_count = 0
        while not passes and auto_revise and revision_count < self.max_revisions:
            revision_count += 1
            print(f"质量未通过，智能修订 (第{revision_count}次)...")

            # 【改进】使用智能修订指导器生成修订版本
            chapter_content = self._smart_revise_chapter(
                context, chapter_content, review_result
            )

            # 重新检查
            review_result = self._review_chapter(chapter_num, chapter_content)
            passes = review_result.get('overall_passes', False)

            if self.use_ai_review and passes:
                ai_review = self.ai_reviewer.deep_review(chapter_num, chapter_content, context)
                if not ai_review.get('overall_passes', True):
                    passes = False

            if not passes:
                time.sleep(self.retry_delay)

        # 保存章节
        self._save_chapter(chapter_num, chapter_info, chapter_content)

        # 更新状态
        word_count = WordCounter.count(chapter_content)['total']
        self._update_chapter_status(chapter_num, word_count, passes, review_result)

        # 【新增】更新记忆库
        self._update_memory_store(chapter_num, chapter_info, chapter_content, review_result)

        # 生成章节摘要（用于后续章节的上下文）
        self._generate_chapter_summary(chapter_num, chapter_content)

        # 更新日志
        self._update_writing_log(chapter_num, chapter_info, chapter_content, review_result, revision_count)

        # Git提交
        title = chapter_info.get('title', f'第{chapter_num}章')
        status = "[OK]" if passes else "[REVISED]" if revision_count > 0 else "[!]"
        if self.git_helper.is_available():
            self.git_helper.add_and_commit(f"{status} {title} ({word_count}字)")

        return {
            'success': True,
            'chapter': chapter_num,
            'title': title,
            'word_count': word_count,
            'passes': passes,
            'review': review_result,
            'revisions': revision_count
        }

    def _smart_revise_chapter(self, context: Dict, original_content: str,
                               review_result: Dict) -> str:
        """
        智能修订章节 - 使用RevisionGuide生成针对性修订

        Args:
            context: 上下文
            original_content: 原始内容
            review_result: 审查结果

        Returns:
            修订后的内容
        """
        # 生成修订指导
        guide = self.revision_guide.generate_revision_guide(
            original_content, review_result, context
        )

        if not guide['needs_revision']:
            return original_content

        # 使用AI进行针对性修订
        try:
            revised = self.revision_guide.generate_ai_revision(
                original_content, review_result, context
            )
            return revised
        except Exception as e:
            print(f"  智能修订失败，使用传统方式: {e}")
            # 回退到传统修订方式
            return self._revise_chapter(context, original_content, review_result)

    def _update_memory_store(self, chapter_num: int, chapter_info: Dict,
                              content: str, review_result: Dict):
        """
        更新记忆库

        Args:
            chapter_num: 章节号
            chapter_info: 章节信息
            content: 章节内容
            review_result: 审查结果
        """
        # 更新章节摘要
        summary = chapter_info.get('summary', content[:200])
        key_events = chapter_info.get('key_events', [])
        self.memory_store.add_chapter_summary(chapter_num, summary, key_events)

        # 更新伏笔状态
        for f_plant in chapter_info.get('foreshadowing_plant', []):
            if f_plant:
                self.memory_store.plant_foreshadowing(
                    chapter_num, f_plant, f_plant
                )

        for f_resolve in chapter_info.get('foreshadowing_resolve', []):
            if f_resolve:
                self.memory_store.resolve_foreshadowing(
                    chapter_num, f_resolve
                )

        # 记录发现的不一致
        for issue in review_result.get('issues', []):
            if issue.get('severity') in ['critical', 'warning']:
                self.memory_store.record_inconsistency(
                    chapter_num,
                    issue.get('check', issue.get('type', 'unknown')),
                    issue.get('description', ''),
                    {'suggestion': issue.get('suggestion', '')}
                )

    def run_batch(self, count: int = 10, stop_on_fail: bool = True) -> Dict:
        """
        批量写作

        Args:
            count: 写作章节数量
            stop_on_fail: 失败时是否停止

        Returns:
            批量写作结果
        """
        results = []
        success_count = 0
        fail_count = 0

        print(f"开始批量写作，目标: {count} 章")
        print("=" * 50)

        for i in range(count):
            chapter_num = self._get_next_chapter()
            if chapter_num is None:
                print("所有章节已完成!")
                break

            print(f"\n[{i+1}/{count}] 处理第 {chapter_num} 章")

            result = self.run(chapter_num, auto_revise=True)
            results.append(result)

            if result['success']:
                success_count += 1
                status = "OK" if result['passes'] else "REVISED"
                print(f"  -> [{status}] {result['word_count']}字, 修订{result['revisions']}次")
            else:
                fail_count += 1
                print(f"  -> 失败: {result.get('message', '')}")
                if stop_on_fail:
                    print("遇到失败，停止批量写作")
                    break

        print("\n" + "=" * 50)
        print(f"批量写作完成: 成功 {success_count}, 失败 {fail_count}")

        # 更新整体状态
        self._update_global_status()

        return {
            'total_attempted': len(results),
            'success_count': success_count,
            'fail_count': fail_count,
            'results': results
        }

    def run_all(self) -> Dict:
        """写完所有剩余章节"""
        total = len([ch for ch in self.chapter_list.get('chapters', []) if not ch.get('passes', False)])
        print(f"开始自动写作，剩余 {total} 章")
        return self.run_batch(count=total, stop_on_fail=True)

    def _get_next_chapter(self) -> Optional[int]:
        for ch in self.chapter_list.get('chapters', []):
            if not ch.get('passes', False):
                return ch.get('number')
        return None

    def _get_chapter_info(self, chapter_num: int) -> Optional[Dict]:
        for ch in self.chapter_list.get('chapters', []):
            if ch.get('number') == chapter_num:
                return ch
        return None

    def _build_context(self, chapter_num: int, chapter_info: Dict) -> Dict:
        """构建写作上下文"""
        context = {
            'chapter_num': chapter_num,
            'chapter_info': chapter_info,
            'writing_standards': self.chapter_list.get('writing_standards', {}),
            'characters': {},
            'previous_chapters': [],
            'chapter_summaries': [],
            'world_rules': self.world_rules,
            'foreshadowing': self.foreshadowing,
            'writing_guide': self.writing_guide,
            'characters_json': self.characters,
            'outline': self.chapter_list
        }

        # 获取涉及的人物
        character_ids = chapter_info.get('characters_involved', [])
        pov_character = chapter_info.get('pov_character', '')

        for char_type in ['protagonists', 'antagonists', 'supporting']:
            for char in self.characters.get(char_type, []):
                char_id = char.get('id', '')
                if char_id in character_ids or char_id == pov_character:
                    context['characters'][char_id] = char

        # 获取前3章内容和摘要
        for i in range(max(1, chapter_num - 3), chapter_num):
            prev_files = self.file_manager.list_files('chapters', f'chapter_{i:03d}*.md')
            if prev_files:
                content = self.file_manager.read_markdown(prev_files[0])
                if content:
                    # 获取摘要
                    summary = self._get_chapter_summary(i)
                    context['chapter_summaries'].append({
                        'chapter': i,
                        'summary': summary,
                        'content_preview': content[:1500]
                    })
                    context['previous_chapters'].append({
                        'chapter': i,
                        'content': content[:2000]
                    })

        return context

    def _get_chapter_summary(self, chapter_num: int) -> str:
        """获取章节摘要"""
        # 尝试从章节信息中获取
        chapter_info = self._get_chapter_info(chapter_num)
        if chapter_info and chapter_info.get('summary'):
            return chapter_info['summary']

        # 从章节文件生成摘要
        files = self.file_manager.list_files('chapters', f'chapter_{chapter_num:03d}*.md')
        if files:
            content = self.file_manager.read_markdown(files[0])
            if content:
                # 简单截取前200字作为摘要
                if content.startswith('#'):
                    content = content.split('\n', 1)[1] if '\n' in content else ''
                return content[:200] + '...'

        return ''

    def _generate_chapter(self, context: Dict) -> str:
        """生成章节内容"""
        prompt = self._build_writer_prompt(context)

        if self.api_config.get('api_key') or self.api_config.get('enabled', False):
            try:
                client = get_client(self.api_config)
                print("  调用API生成...")
                system_prompt = self._load_system_prompt()
                content = client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=self.api_config.get('max_tokens', 4096),
                    temperature=self.api_config.get('temperature', 0.7)
                )
                return content
            except Exception as e:
                print(f"  API调用失败: {e}")

        return "[API未配置，无法生成内容]"

    def _revise_chapter(self, context: Dict, original_content: str, review: Dict) -> str:
        """修订章节"""
        issues = review.get('issues', [])
        issues_text = '\n'.join(f"- [{i['type']}] {i['description']}" for i in issues)

        prompt = f"""你需要修订以下小说章节。

## 原始章节

{original_content[:3000]}

## 需要修复的问题

{issues_text}

## 修订要求

1. 保持原有剧情框架
2. 针对每个问题进行修复
3. 确保字数在2500-5000之间
4. 保持风格一致

请输出修订后的完整章节内容。"""

        try:
            client = get_client(self.api_config)
            content = client.generate(
                prompt=prompt,
                max_tokens=self.api_config.get('max_tokens', 4096),
                temperature=self.api_config.get('temperature', 0.7)
            )
            return content
        except Exception as e:
            print(f"  修订失败: {e}")
            return original_content

    def _build_writer_prompt(self, context: Dict) -> str:
        """构建写作提示词"""
        chapter_info = context['chapter_info']
        writing_standards = context['writing_standards']

        # 人物信息
        char_info = ""
        for char_id, char in context['characters'].items():
            char_info += f"\n### {char.get('name', '未知')}\n"
            char_info += f"- 性格: {', '.join(char.get('personality', {}).get('traits', []))}\n"
            char_info += f"- 缺陷: {', '.join(char.get('personality', {}).get('flaws', []))}\n"
            char_info += f"- 背景: {char.get('background', '')[:200]}\n"
            char_info += f"- 动机: {char.get('motivation', '')}\n"

        # 前文摘要
        prev_summary = ""
        for item in context.get('chapter_summaries', [])[-3:]:
            prev_summary += f"\n**第{item['chapter']}章**: {item['summary']}\n"

        # 伏笔
        foreshadowing_plant = chapter_info.get('foreshadowing_plant', [])
        foreshadowing_resolve = chapter_info.get('foreshadowing_resolve', [])

        # 世界观
        world_info = ""
        if context['world_rules'].get('tech_system'):
            tech = context['world_rules']['tech_system']
            world_info += f"科技水平: {tech.get('tech_level', '')}\n"
            world_info += f"科技规则: {', '.join(tech.get('tech_rules', []))}\n"
        if context['world_rules'].get('magic_system'):
            magic = context['world_rules']['magic_system']
            world_info += f"魔法类型: {magic.get('magic_type', '')}\n"
            world_info += f"限制: {', '.join(magic.get('costs_and_limits', []))}\n"

        prompt = f"""# 写作任务

撰写第 {context['chapter_num']} 章：「{chapter_info.get('title', '')}」

## 基本信息

| 项目 | 内容 |
|------|------|
| 字数 | {writing_standards.get('min_words_per_chapter', 2500)}-{writing_standards.get('max_words_per_chapter', 5000)} 字 |
| POV | {writing_standards.get('pov_style', '第三人称')} |
| 主视角 | {chapter_info.get('pov_character', '')} |

## 本章概要

{chapter_info.get('summary', '待创作')}

## 关键事件

{chr(10).join('- ' + e for e in chapter_info.get('key_events', []))}

## 涉及人物

{char_info if char_info else "主角"}

## 前情提要

{prev_summary if prev_summary else "这是第一章"}

## 世界设定

{world_info if world_info else "通用设定"}

## 伏笔处理

需要埋设: {', '.join(foreshadowing_plant) if foreshadowing_plant else '无'}
需要回收: {', '.join(foreshadowing_resolve) if foreshadowing_resolve else '无'}

## 结尾悬念

{chapter_info.get('cliffhanger', '设计一个引人入胜的结尾')}

---

## 写作要求

1. 直接输出正文，不要标题
2. 字数必须在{writing_standards.get('min_words_per_chapter', 2500)}-{writing_standards.get('max_words_per_chapter', 5000)}之间
3. 场景转换用 *** 分隔
4. 对话独占一行
5. 结尾要有悬念
"""
        return prompt

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / 'prompts' / 'writer.md'
        if prompt_path.exists():
            content = prompt_path.read_text(encoding='utf-8')
            parts = content.split('---')
            return parts[0].strip() if parts else content
        return "你是一位专业的科幻/奇幻小说作家，擅长创作引人入胜的故事。"

    def _generate_chapter_summary(self, chapter_num: int, content: str):
        """生成并保存章节摘要"""
        # 提取正文（去掉标题）
        if content.startswith('#'):
            content = content.split('\n', 1)[1] if '\n' in content else ''

        # 调用API生成摘要
        if self.api_config.get('api_key') or self.api_config.get('enabled', False):
            try:
                client = get_client(self.api_config)
                prompt = f"""请为以下小说章节生成一个50-100字的摘要，概括主要剧情：

{content[:2000]}

只输出摘要，不要其他内容。"""

                summary = client.generate(prompt, max_tokens=200, temperature=0.5)

                # 更新章节信息
                for ch in self.chapter_list.get('chapters', []):
                    if ch.get('number') == chapter_num:
                        ch['summary'] = summary.strip()
                        break

                self.file_manager.write_json('chapter_list.json', self.chapter_list)
            except:
                pass

    def _review_chapter(self, chapter_num: int, content: str) -> Dict:
        return self.reviewer.review_chapter(chapter_num, content)

    def _save_chapter(self, chapter_num: int, chapter_info: Dict, content: str):
        title = chapter_info.get('title', f'第{chapter_num}章')
        full_content = f"# {title}\n\n{content}"
        filename = f"chapters/chapter_{chapter_num:03d}.md"
        self.file_manager.write_markdown(filename, full_content)

    def _update_chapter_status(self, chapter_num: int, word_count: int, passes: bool, review: Dict):
        for ch in self.chapter_list.get('chapters', []):
            if ch.get('number') == chapter_num:
                ch['word_actual'] = word_count
                ch['passes'] = passes
                ch['quality_notes'] = review.get('summary', '')
                break

        status = self.chapter_list.get('status', {})
        if passes:
            status['completed_chapters'] = status.get('completed_chapters', 0) + 1
            status['completed_words'] = status.get('completed_words', 0) + word_count
        status['last_session'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.chapter_list['status'] = status

        self.file_manager.write_json('chapter_list.json', self.chapter_list)

        if self.quality_checklist:
            chapter_result = {
                'chapter': chapter_num,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'overall_passes': passes,
                'checks': review.get('checks', {}),
                'issues': review.get('issues', []),
                'summary': review.get('summary', '')
            }
            self.quality_checklist.setdefault('chapter_results', []).append(chapter_result)
            self.file_manager.write_json('quality_checklist.json', self.quality_checklist)

    def _update_global_status(self):
        """更新全局状态"""
        total = len(self.chapter_list.get('chapters', []))
        completed = sum(1 for ch in self.chapter_list.get('chapters', []) if ch.get('passes', False))
        words = sum(ch.get('word_actual', 0) for ch in self.chapter_list.get('chapters', []) if ch.get('passes', False))

        status = self.chapter_list.get('status', {})
        status['completed_chapters'] = completed
        status['completed_words'] = words
        status['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.chapter_list['status'] = status

        self.file_manager.write_json('chapter_list.json', self.chapter_list)

    def _update_writing_log(self, chapter_num: int, chapter_info: Dict,
                           content: str, review: Dict, revisions: int):
        title = chapter_info.get('title', f'第{chapter_num}章')
        word_count = WordCounter.count(content)['total']
        passes = review.get('overall_passes', False)

        existing_log = self.file_manager.read_markdown('writing_log.md') or ''
        session_num = existing_log.count('### 会话') + 1

        status_text = "通过" if passes else f"修订{revisions}次后通过" if revisions > 0 else "待修订"

        new_entry = f"""
### 会话 #{session_num} - {datetime.now().strftime('%Y-%m-%d %H:%M')}

- **类型**：写作
- **章节**：{title}
- **字数**：{word_count:,}
- **状态**：{status_text}
- **检查**：{review.get('summary', '')}
- **下次**：第{chapter_num + 1}章

"""
        self.file_manager.append_text('writing_log.md', new_entry)

    def get_status(self) -> Dict:
        meta = self.chapter_list.get('meta', {})
        status = self.chapter_list.get('status', {})
        next_chapter = self._get_next_chapter()

        return {
            'project_path': str(self.project_path),
            'title': meta.get('title', '未命名'),
            'genre': meta.get('genre', ''),
            'completed_chapters': status.get('completed_chapters', 0),
            'total_chapters': meta.get('total_chapters', 0),
            'completed_words': status.get('completed_words', 0),
            'target_words': meta.get('total_words_target', 0),
            'next_chapter': next_chapter,
            'current_volume': status.get('current_volume', 1),
            'last_updated': status.get('last_updated', '')
        }
