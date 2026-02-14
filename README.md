# 长篇小说自动创作系统

基于 Anthropic 文章 "Effective harnesses for long-running agents" 理论设计的**双重代理架构**自动小说创作系统。

## 功能特点

- **双重代理架构**：初始化代理 + 写作代理
- **支持长篇创作**：50-100万字规模
- **专注科幻/奇幻**：完善的世界观、科技/魔法体系支持
- **质量保证**：自动一致性检查、伏笔追踪
- **版本控制**：集成 Git 追踪每次创作

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   novel_manager.py                   │
│                     (CLI 入口)                       │
└─────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │Initializer│    │  Writer  │    │ Reviewer │
    │   Agent   │    │  Agent   │    │  Agent   │
    └──────────┘    └──────────┘    └──────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
    ┌─────────────────────────────────────────────────┐
    │                  项目文件结构                     │
    │  ├── novel_blueprint.json (蓝图)                │
    │  ├── world_rules/       (世界规则)              │
    │  ├── characters.json    (人物档案)              │
    │  ├── outline.json       (章节大纲)              │
    │  ├── writing_log.md     (创作日志)              │
    │  └── chapters/          (章节文件)              │
    └─────────────────────────────────────────────────┘
```

## 安装

```bash
# 克隆项目
git clone <repository_url>
cd long-running

# 安装依赖
pip install -r requirements.txt
```

## API 配置（重要）

系统需要配置 LLM API 才能生成实际的小说内容。

### 方式一：环境变量（推荐）

```bash
# Windows (CMD)
set ANTHROPIC_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your_api_key_here"

# Linux/macOS
export ANTHROPIC_API_KEY=your_api_key_here
```

### 方式二：配置文件

编辑 `config.yaml`：

```yaml
api:
  enabled: true           # 启用API调用
  provider: anthropic     # 或 openai
  api_key: sk-ant-xxx     # 你的API密钥
  model: claude-sonnet-4-20250514
```

### 方式三：.env 文件

```bash
# 复制模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
ANTHROPIC_API_KEY=your_api_key_here
```

### 获取 API Key

| 提供商 | 获取地址 | 推荐模型 |
|--------|----------|----------|
| Anthropic | https://console.anthropic.com/ | claude-sonnet-4-20250514 |
| OpenAI | https://platform.openai.com/api-keys | gpt-4-turbo-preview |

### 验证配置

```bash
# 如果未配置API，系统会生成占位符内容并提示
python novel_manager.py write

# 配置成功后，系统会调用API生成实际内容
```

## 快速开始

### 1. 初始化新项目

```bash
# 基本初始化
python novel_manager.py init "帮我写一部太空歌剧，讲述一个退役飞行员意外获得神秘信号，被卷入银河阴谋的故事"

# 使用模板
python novel_manager.py init "太空歌剧" --template sci-fi --name my_space_opera
```

### 2. 开始写作

```bash
# 写下一章
python novel_manager.py write

# 写指定章节
python novel_manager.py write --chapter 5
```

### 3. 查看状态

```bash
python novel_manager.py status
```

### 4. 质量检查

```bash
# 检查最近章节
python novel_manager.py review

# 全面检查
python novel_manager.py review --all
```

### 5. 导出

```bash
# 导出为文本
python novel_manager.py export

# 导出为HTML
python novel_manager.py export --format html

# 指定输出路径
python novel_manager.py export --format markdown --output ./my_novel.md
```

## CLI 命令详解

| 命令 | 说明 |
|------|------|
| `init` | 初始化新小说项目 |
| `write` | 继续写作（写下一章或指定章节）|
| `status` | 查看当前项目状态 |
| `review` | 质量检查 |
| `export` | 导出小说 |
| `list` | 列出所有项目 |
| `switch` | 切换当前项目 |
| `log` | 查看创作日志 |

## 项目文件结构

```
novel-project/
├── novel_blueprint.json    # 小说总蓝图
├── world_rules/            # 世界规则目录
│   ├── tech_system.json    # 科技体系（科幻）
│   ├── magic_system.json   # 魔法体系（奇幻）
│   ├── factions.json       # 势力阵营
│   ├── locations.json      # 重要地点
│   ├── terminology.json    # 专有名词
│   └── timeline.json       # 时间线
├── characters.json         # 人物档案
├── outline.json            # 章节大纲
├── quality_check.json      # 质量检查记录
├── writing_log.md          # 创作日志
└── chapters/               # 章节目录
    ├── chapter_001.md
    ├── chapter_002.md
    └── ...
```

## 核心数据结构

### novel_blueprint.json

```json
{
  "meta": {
    "title": "小说标题",
    "genre": "科幻/奇幻",
    "target_words": 800000,
    "target_chapters": 200,
    "volumes": 4
  },
  "status": {
    "completed_chapters": 0,
    "total_words": 0
  },
  "writing_standards": {
    "min_words_per_chapter": 2500,
    "max_words_per_chapter": 5000
  }
}
```

## 配置说明

编辑 `config.yaml` 进行配置：

```yaml
api:
  provider: anthropic
  model: claude-sonnet-4-20250514
  max_tokens: 64000
  temperature: 0.7

writing:
  chapter_min_words: 2500
  chapter_max_words: 5000
  auto_review: true
  auto_commit: true
```

## 与 Claude API 集成

系统设计为与 Claude API 配合使用：

1. **初始化时**：调用 Claude 生成世界观、人物、大纲
2. **写作时**：调用 Claude 生成章节内容
3. **审查时**：可调用 Claude 进行智能审查

API 调用代码示例：

```python
import anthropic

client = anthropic.Anthropic()

def generate_chapter(prompt: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=64000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text
```

## 质量检查

系统自动进行以下检查：

- **字数检查**：确保每章在2500-5000字范围内
- **POV一致性**：检查视角是否统一
- **人物一致性**：检查人物行为是否符合设定
- **世界观检查**：检查是否违反科技/魔法规则
- **术语检查**：检查专有名词使用是否正确
- **伏笔追踪**：检查伏笔是否正确埋设和回应

## 工作流程

```
┌─────────────┐
│ 用户描述需求 │
└──────┬──────┘
       ▼
┌─────────────┐
│ 初始化代理   │ ──→ 生成世界/人物/大纲
└──────┬──────┘
       ▼
┌─────────────┐
│ 写作代理    │ ──→ 生成章节
└──────┬──────┘
       ▼
┌─────────────┐
│ 质量检查    │ ──→ 自动审查
└──────┬──────┘
       ▼
┌─────────────┐
│ 更新文件    │ ──→ 保存 + Git提交
└──────┬──────┘
       ▼
    循环...
```

## 许可证

MIT License
