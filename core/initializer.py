"""
初始化代理模块 - 完全自动化版本

核心改进：
1. 调用API生成详细世界观
2. 调用API生成详细人物
3. 调用API生成详细大纲
4. 调用API规划伏笔
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from utils.file_manager import FileManager
from utils.git_helper import GitHelper
from utils.api_client import get_client


class Initializer:
    """
    初始化代理 - 完全自动化

    职责：
    1. 理解用户需求
    2. 调用API生成完整世界观
    3. 调用API生成详细人物档案
    4. 调用API生成章节大纲
    5. 调用API规划伏笔
    6. 创建所有项目文件
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_config = self.config.get('api', {})

    def run(self, description: str, project_name: str = None, template: str = None,
            auto_generate: bool = True) -> Dict:
        """
        运行初始化代理

        Args:
            description: 用户对小说的描述
            project_name: 项目名称
            template: 模板类型
            auto_generate: 是否调用API自动生成内容

        Returns:
            初始化结果
        """
        # 1. 确定项目名称和路径
        if not project_name:
            project_name = self._generate_project_name(description)

        project_path = self._get_project_path(project_name)

        # 2. 创建项目目录结构
        self._create_project_structure(project_path)

        # 3. 初始化文件管理器
        file_manager = FileManager(project_path)
        git_helper = GitHelper(project_path)

        # 4. 检测小说类型
        genre = self._detect_genre(description, template)

        # 5. 生成项目文件
        if auto_generate and (self.api_config.get('api_key') or self.api_config.get('enabled', False)):
            # 调用API生成详细内容
            print("正在调用API生成小说框架...")

            world_rules = self._api_generate_world_rules(description, genre)
            characters = self._api_generate_characters(description, genre, world_rules)
            chapter_list = self._api_generate_chapter_list(description, genre, world_rules, characters)
            foreshadowing = self._api_generate_foreshadowing(chapter_list)
        else:
            # 使用模板生成基础结构
            print("使用模板生成基础框架...")
            chapter_list = self._generate_chapter_list(description, genre, template)
            world_rules = self._generate_world_rules(genre, description)
            characters = self._generate_characters(genre, description)
            foreshadowing = self._generate_foreshadowing()

        # 6. 生成其他文件
        quality_checklist = self._generate_quality_checklist()
        writing_guide = self._generate_writing_guide(genre, world_rules)

        # 7. 保存所有文件
        self._save_project_files(file_manager, {
            'chapter_list': chapter_list,
            'world_rules': world_rules,
            'characters': characters,
            'foreshadowing': foreshadowing,
            'quality_checklist': quality_checklist,
            'writing_guide': writing_guide
        })

        # 8. 初始化创作日志
        self._init_writing_log(file_manager, description, chapter_list, auto_generate)

        # 9. Git初始提交
        if git_helper.is_available():
            title = chapter_list['meta']['title']
            git_helper.add_and_commit(f"初始化小说项目: {title}")

        return {
            'success': True,
            'project_name': project_name,
            'project_path': str(project_path),
            'title': chapter_list['meta']['title'],
            'total_chapters': chapter_list['meta']['total_chapters'],
            'total_words_target': chapter_list['meta']['total_words_target'],
            'auto_generated': auto_generate
        }

    def _get_api_client(self):
        """获取API客户端"""
        return get_client(self.api_config)

    def _api_generate_world_rules(self, description: str, genre: str) -> Dict:
        """调用API生成世界规则"""
        prompt = f"""你需要为一部{genre}小说创建详细的世界观设定。

用户描述：{description}

请以JSON格式输出世界观设定，包含以下内容：

```json
{{
  "tech_system": {{
    "tech_level": "科技水平",
    "key_technologies": [
      {{"name": "技术名称", "description": "描述", "limitations": ["限制条件"]}}
    ],
    "tech_rules": ["科技规则1", "科技规则2"]
  }},
  "magic_system": {{
    "magic_type": "魔法类型（奇幻用）",
    "power_source": "力量来源",
    "tiers": [{{"level": 1, "name": "等级名", "capabilities": []}}],
    "costs_and_limits": ["代价和限制"]
  }},
  "factions": [
    {{"id": "faction_001", "name": "势力名称", "philosophy": "理念", "territory": [], "relations": {{}}}}
  ],
  "locations": [
    {{"id": "loc_001", "name": "地点名称", "description": "描述", "significance": "重要性"}}
  ],
  "terminology": [
    {{"term": "术语", "definition": "定义", "usage_notes": "使用说明"}}
  ],
  "timeline": [
    {{"year": 2150, "event": "事件", "significance": "意义"}}
  ]
}}
```

注意：
1. 科技/魔法体系必须有明确的限制和代价
2. 势力之间要有复杂的关系
3. 术语要前后一致
4. 只输出JSON，不要其他内容"""

        try:
            client = self._get_api_client()
            print("  - 生成世界规则...")
            response = client.generate(prompt, max_tokens=4000, temperature=0.7)

            # 提取JSON
            json_str = self._extract_json(response)
            if json_str:
                return json.loads(json_str)
        except Exception as e:
            print(f"  - API调用失败: {e}")

        # 失败时返回模板
        return self._generate_world_rules(genre, description)

    def _api_generate_characters(self, description: str, genre: str, world_rules: Dict) -> Dict:
        """调用API生成人物"""
        world_context = json.dumps(world_rules, ensure_ascii=False, indent=2)[:2000]

        prompt = f"""你需要为一部{genre}小说创建详细的人物设定。

小说描述：{description}

世界观背景：
{world_context}

请以JSON格式输出人物设定：

```json
{{
  "protagonists": [
    {{
      "id": "char_001",
      "name": "姓名",
      "role": "主角",
      "age": 25,
      "personality": {{
        "traits": ["优点1", "优点2"],
        "flaws": ["缺陷1", "缺陷2"]
      }},
      "background": "背景故事",
      "motivation": "核心动机",
      "abilities": ["能力1"],
      "character_arc": {{
        "start_state": "起始状态",
        "end_state": "目标状态",
        "key_milestones": [{{"chapter": 10, "milestone": "里程碑"}}]
      }},
      "relationships": [
        {{"target_id": "char_002", "relation": "关系", "development": "发展"}}
      ]
    }}
  ],
  "antagonists": [...],
  "supporting": [...]
}}
```

要求：
1. 主角必须有明显的性格缺陷
2. 每个人物都要有独特的话语风格
3. 人物之间要有复杂的关系网
4. 只输出JSON"""

        try:
            client = self._get_api_client()
            print("  - 生成人物档案...")
            response = client.generate(prompt, max_tokens=4000, temperature=0.7)

            json_str = self._extract_json(response)
            if json_str:
                return json.loads(json_str)
        except Exception as e:
            print(f"  - API调用失败: {e}")

        return self._generate_characters(genre, description)

    def _api_generate_chapter_list(self, description: str, genre: str,
                                   world_rules: Dict, characters: Dict) -> Dict:
        """调用API生成章节大纲"""
        # 获取主要人物名字
        char_names = []
        for char in characters.get('protagonists', [])[:3]:
            char_names.append(char.get('name', '主角'))

        prompt = f"""你需要为一部{genre}长篇小说创建详细的章节大纲。

小说描述：{description}

主要人物：{', '.join(char_names)}

请以JSON格式输出前30章的详细大纲：

```json
{{
  "meta": {{
    "title": "小说标题",
    "genre": "{genre}",
    "total_chapters": 200,
    "total_words_target": 800000,
    "volumes": 4,
    "themes": ["主题1", "主题2"]
  }},
  "volumes": [
    {{"id": 1, "name": "第一卷名称", "chapters": [1, 50], "summary": "本卷概要"}}
  ],
  "writing_standards": {{
    "min_words_per_chapter": 2500,
    "max_words_per_chapter": 5000,
    "pov_style": "第三人称限制视角",
    "tone": "风格描述"
  }},
  "chapters": [
    {{
      "number": 1,
      "title": "第一章 标题",
      "volume": 1,
      "word_target": 3000,
      "summary": "本章概要（50-100字）",
      "key_events": ["事件1", "事件2", "事件3"],
      "pov_character": "char_001",
      "characters_involved": ["char_001"],
      "locations": ["地点"],
      "cliffhanger": "结尾悬念"
    }}
  ]
}}
```

要求：
1. 每章必须有具体的key_events
2. 要有明确的故事推进节奏
3. 开篇要快，逐步展开世界观
4. 只输出JSON，生成前30章详细大纲"""

        try:
            client = self._get_api_client()
            print("  - 生成章节大纲...")
            response = client.generate(prompt, max_tokens=8000, temperature=0.7)

            json_str = self._extract_json(response)
            if json_str:
                chapter_list = json.loads(json_str)

                # 补充剩余章节（31-200章简化版）
                existing_count = len(chapter_list.get('chapters', []))
                total = chapter_list.get('meta', {}).get('total_chapters', 200)

                for i in range(existing_count + 1, total + 1):
                    volume = (i - 1) // 50 + 1
                    chapter_list['chapters'].append({
                        "number": i,
                        "title": f"第{i}章",
                        "volume": volume,
                        "word_target": 3000,
                        "word_actual": 0,
                        "summary": "",
                        "key_events": [],
                        "pov_character": "char_001",
                        "characters_involved": ["char_001"],
                        "locations": [],
                        "foreshadowing_plant": [],
                        "foreshadowing_resolve": [],
                        "cliffhanger": "",
                        "passes": False,
                        "quality_notes": ""
                    })

                # 添加状态字段
                chapter_list['status'] = {
                    "completed_chapters": 0,
                    "completed_words": 0,
                    "last_session": None,
                    "current_volume": 1,
                    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                # 为已有章节添加缺失字段
                for ch in chapter_list.get('chapters', []):
                    ch['word_actual'] = ch.get('word_actual', 0)
                    ch['foreshadowing_plant'] = ch.get('foreshadowing_plant', [])
                    ch['foreshadowing_resolve'] = ch.get('foreshadowing_resolve', [])
                    ch['passes'] = ch.get('passes', False)
                    ch['quality_notes'] = ch.get('quality_notes', '')

                return chapter_list
        except Exception as e:
            print(f"  - API调用失败: {e}")

        return self._generate_chapter_list(description, genre, None)

    def _api_generate_foreshadowing(self, chapter_list: Dict) -> Dict:
        """调用API生成伏笔规划"""
        # 提取前30章的大纲
        chapters_summary = []
        for ch in chapter_list.get('chapters', [])[:30]:
            chapters_summary.append({
                'number': ch.get('number'),
                'title': ch.get('title'),
                'summary': ch.get('summary', '')
            })

        prompt = f"""根据以下章节大纲，规划小说的伏笔：

{json.dumps(chapters_summary, ensure_ascii=False, indent=2)}

请以JSON格式输出伏笔规划：

```json
{{
  "items": [
    {{
      "id": "f001",
      "description": "伏笔描述",
      "type": "major",
      "hint": "暗示内容",
      "plant_chapter": 1,
      "resolve_chapter": 30,
      "status": "pending"
    }}
  ]
}}
```

要求：
1. 规划5-10个主要伏笔
2. 伏笔要有跨章节/跨卷的效果
3. major类型伏笔影响主线，minor类型伏笔丰富细节
4. 只输出JSON"""

        try:
            client = self._get_api_client()
            print("  - 规划伏笔...")
            response = client.generate(prompt, max_tokens=2000, temperature=0.7)

            json_str = self._extract_json(response)
            if json_str:
                foreshadowing = json.loads(json_str)

                # 将伏笔信息同步到章节列表
                for item in foreshadowing.get('items', []):
                    plant_ch = item.get('plant_chapter')
                    resolve_ch = item.get('resolve_chapter')

                    if plant_ch and plant_ch <= len(chapter_list.get('chapters', [])):
                        chapter_list['chapters'][plant_ch - 1].setdefault('foreshadowing_plant', [])
                        chapter_list['chapters'][plant_ch - 1]['foreshadowing_plant'].append(
                            item.get('description', '')
                        )

                    if resolve_ch and resolve_ch <= len(chapter_list.get('chapters', [])):
                        chapter_list['chapters'][resolve_ch - 1].setdefault('foreshadowing_resolve', [])
                        chapter_list['chapters'][resolve_ch - 1]['foreshadowing_resolve'].append(
                            item.get('description', '')
                        )

                return foreshadowing
        except Exception as e:
            print(f"  - API调用失败: {e}")

        return {"items": []}

    def _extract_json(self, text: str) -> Optional[str]:
        """从文本中提取JSON"""
        import re

        # 尝试找到 ```json ... ``` 块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_match:
            return json_match.group(1).strip()

        # 尝试找到 { ... } 块
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            return brace_match.group(0)

        return None

    # 保留原有的辅助方法
    def _generate_project_name(self, description: str) -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"novel_{timestamp}"

    def _get_project_path(self, project_name: str) -> Path:
        base_path = self.config.get('project', {}).get('default_location', './novels')
        return Path(base_path) / project_name

    def _create_project_structure(self, project_path: Path):
        dirs = ['', 'world_rules', 'chapters', 'exports']
        for d in dirs:
            (project_path / d).mkdir(parents=True, exist_ok=True)

    def _detect_genre(self, description: str, template: str = None) -> str:
        if template:
            return {'sci-fi': '科幻', 'fantasy': '奇幻', 'generic': '通用'}.get(template, '通用')

        sci_fi_keywords = ['太空', '宇宙', '飞船', '科技', 'AI', '机器人', '未来', '星际', '赛博', '霓虹']
        fantasy_keywords = ['魔法', '龙', '剑', '奇幻', '精灵', '巫师', '王国', '修炼', '仙侠']

        for kw in sci_fi_keywords:
            if kw in description:
                return '科幻'
        for kw in fantasy_keywords:
            if kw in description:
                return '奇幻'
        return '通用'

    def _generate_chapter_list(self, description: str, genre: str, template: str = None) -> Dict:
        """生成基础章节清单（不调用API时的回退）"""
        total_chapters = 200
        total_words = 800000
        volumes = 4

        chapters_per_volume = total_chapters // volumes

        volume_list = []
        for i in range(1, volumes + 1):
            start_ch = (i - 1) * chapters_per_volume + 1
            end_ch = i * chapters_per_volume if i < volumes else total_chapters
            volume_list.append({
                "id": i,
                "name": f"第{['一','二','三','四'][i-1]}卷",
                "chapters": [start_ch, end_ch],
                "word_target": total_words // volumes,
                "summary": "",
                "themes": []
            })

        chapters = []
        for i in range(1, total_chapters + 1):
            chapters.append({
                "number": i,
                "title": f"第{i}章",
                "volume": (i - 1) // chapters_per_volume + 1,
                "word_target": 3000,
                "word_actual": 0,
                "summary": f"第{i}章内容" if i <= 20 else "",
                "key_events": [],
                "pov_character": "char_001",
                "characters_involved": ["char_001"],
                "locations": [],
                "foreshadowing_plant": [],
                "foreshadowing_resolve": [],
                "cliffhanger": "",
                "passes": False,
                "quality_notes": ""
            })

        return {
            "meta": {
                "title": "待定标题",
                "genre": genre,
                "sub_genre": "",
                "total_chapters": total_chapters,
                "total_words_target": total_words,
                "volumes": volumes,
                "created_at": datetime.now().strftime('%Y-%m-%d'),
                "themes": []
            },
            "status": {
                "completed_chapters": 0,
                "completed_words": 0,
                "last_session": None,
                "current_volume": 1,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            "volumes": volume_list,
            "writing_standards": {
                "min_words_per_chapter": 2500,
                "max_words_per_chapter": 5000,
                "pov_style": "第三人称限制视角",
                "tone": "史诗感与人性化并重"
            },
            "chapters": chapters
        }

    def _generate_world_rules(self, genre: str, description: str) -> Dict:
        if genre == '科幻':
            return {
                "tech_system": {"tech_level": "星际航行时代", "key_technologies": [], "tech_rules": []},
                "magic_system": {},
                "factions": [],
                "locations": [],
                "terminology": [],
                "timeline": []
            }
        elif genre == '奇幻':
            return {
                "tech_system": {},
                "magic_system": {"magic_type": "", "power_source": "", "tiers": [], "costs_and_limits": []},
                "factions": [],
                "locations": [],
                "terminology": [],
                "timeline": []
            }
        return {"tech_system": {}, "magic_system": {}, "factions": [], "locations": [], "terminology": [], "timeline": []}

    def _generate_characters(self, genre: str, description: str) -> Dict:
        return {
            "protagonists": [{
                "id": "char_001",
                "name": "主角",
                "role": "主角",
                "age": 25,
                "personality": {"traits": [], "flaws": []},
                "background": "",
                "motivation": "",
                "character_arc": {"start_state": "", "end_state": "", "key_milestones": []},
                "relationships": []
            }],
            "antagonists": [],
            "supporting": []
        }

    def _generate_foreshadowing(self) -> Dict:
        return {"items": []}

    def _generate_quality_checklist(self) -> Dict:
        return {
            "checks": [
                {"id": "word_count", "name": "字数检查", "description": "2500-5000字", "required": True},
                {"id": "pov_consistency", "name": "视角一致性", "description": "POV无越界", "required": True},
                {"id": "character_consistency", "name": "人物一致性", "description": "行为符合设定", "required": True},
                {"id": "world_rules", "name": "世界规则", "description": "遵守设定", "required": True},
                {"id": "foreshadowing", "name": "伏笔处理", "description": "正确埋设/回收", "required": False},
                {"id": "plot_coherence", "name": "剧情连贯", "description": "逻辑连贯", "required": True}
            ],
            "chapter_results": []
        }

    def _generate_writing_guide(self, genre: str, world_rules: Dict) -> str:
        return f"""# 写作指南

## 风格要求
- 类型：{genre}
- POV：第三人称限制视角
- 每章2500-5000字

## 章节结构
1. 开篇（300字）：场景描写，抛出悬念
2. 发展（2000字）：推进剧情，人物互动
3. 高潮（500字）：核心冲突
4. 收尾（200字）：设置悬念

## 质量要求
- 字数必须在2500-5000之间
- 人物行为必须符合设定
- 遵守世界观规则
- 结尾要有悬念
"""

    def _save_project_files(self, file_manager: FileManager, data: Dict):
        file_manager.write_json('chapter_list.json', data['chapter_list'])

        world_rules = data['world_rules']
        file_manager.ensure_dir('world_rules')
        if world_rules.get('tech_system'):
            file_manager.write_json('world_rules/tech_system.json', world_rules['tech_system'])
        if world_rules.get('magic_system'):
            file_manager.write_json('world_rules/magic_system.json', world_rules['magic_system'])
        if world_rules.get('factions'):
            file_manager.write_json('world_rules/factions.json', {'factions': world_rules['factions']})
        if world_rules.get('locations'):
            file_manager.write_json('world_rules/locations.json', {'locations': world_rules['locations']})
        if world_rules.get('terminology'):
            file_manager.write_json('world_rules/terminology.json', {'terms': world_rules['terminology']})

        file_manager.write_json('characters.json', data['characters'])
        file_manager.write_json('foreshadowing.json', data['foreshadowing'])
        file_manager.write_json('quality_checklist.json', data['quality_checklist'])
        file_manager.write_markdown('writing_guide.md', data['writing_guide'])

    def _init_writing_log(self, file_manager: FileManager, description: str,
                          chapter_list: Dict, auto_generated: bool):
        title = chapter_list['meta']['title']
        total_chapters = chapter_list['meta']['total_chapters']
        total_words = chapter_list['meta']['total_words_target']
        gen_status = "API自动生成" if auto_generated else "模板生成"

        log_content = f"""# 《{title}》创作日志

## 项目信息
- 类型：{chapter_list['meta']['genre']}
- 总章节：{total_chapters}
- 目标字数：{total_words:,}
- 生成方式：{gen_status}

## 会话记录

### 会话 #1 - {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **类型**：初始化
- **工作内容**：
  - 创建小说项目
  - 用户需求：{description[:100]}
  - 生成{total_chapters}章大纲
  - {'已调用API生成世界观、人物、大纲、伏笔' if auto_generated else '使用模板生成基础结构'}
- **下次继续**：`python novel_manager.py write` 或 `python novel_manager.py write --all`

"""
        file_manager.write_markdown('writing_log.md', log_content)
