# 质量控制改进方案总结

## 问题诊断

原始系统的审查模块存在以下问题：

| 问题 | 原因 | 后果 |
|------|------|------|
| 审查是占位符 | `_check_pov_consistency` 等函数几乎为空 | 无法检测真正的问题 |
| 无跨章节追踪 | 只看前3章摘要 | 第100章可能与第10章矛盾 |
| 无全局记忆 | 没有"小说记忆库" | 人物发展弧线断裂 |
| 无AI深度审查 | 仅规则基础检查 | 无法理解语义问题 |
| 修订指导模糊 | 只告诉"有问题" | AI不知如何修改 |

## 新增模块

### 1. AI深度审查器 (`core/ai_reviewer.py`)

**功能**：使用LLM进行语义级别的深度审查

**检查维度**：
- 逻辑一致性
- 人物一致性
- 世界观一致性
- POV一致性
- 伏笔处理
- 与前文连贯性
- 文学质量

**输出**：带分数和具体修改建议的JSON报告

### 2. 全局记忆库 (`core/memory_store.py`)

**功能**：追踪整个小说的关键信息

**追踪内容**：
- 人物状态变化（位置、关系、能力）
- 时间线事件
- 伏笔状态（已埋设/已回收/超期）
- 章节摘要索引
- 发现的不一致记录

**核心方法**：
```python
# 更新人物状态
memory_store.update_character_state(char_id, chapter, state_update)

# 伏笔追踪
memory_store.plant_foreshadowing(chapter, foreshadow_id, description)
memory_store.resolve_foreshadowing(chapter, foreshadow_id)

# 获取超期伏笔
overdue = memory_store.get_overdue_foreshadowing(current_chapter, threshold=50)
```

### 3. 智能修订指导器 (`core/revision_guide.py`)

**功能**：不只是告诉AI"有问题"，而是指导它"怎么改"

**工作流程**：
1. 分析审查结果，按优先级排序问题
2. 生成具体的修订指导文档
3. 创建针对性修订提示词
4. 调用AI进行修订

**输出示例**：
```
## 修订指导

### 逻辑一致性
❗ **问题 1** (critical)
   - 位置: "他从未见过这把剑..."
   - 问题: 与第5章描述矛盾，主角曾在第5章使用过这把剑
   - 修改建议: 改为"他再次握住这把剑，回想起第一次..."
```

### 4. 跨章节一致性检查器 (`core/consistency_checker.py`)

**功能**：在关键节点进行全局一致性检查

**检查级别**：

| 级别 | 触发频率 | 检查内容 |
|------|----------|----------|
| per_chapter | 每章 | 与前章连贯性、基本人物状态 |
| minor | 每10章 | 最近10章连贯性、伏笔状态、人物弧线 |
| major | 每50章 | 全局一致性、所有伏笔、时间线、AI深度分析 |
| volume_end | 每卷结束 | 卷内所有检查 |

## 工作流程对比

### 改进前

```
写作 → 规则检查（占位符）→ 通过/重试
```

### 改进后

```
写作
  ↓
规则基础检查
  ↓
AI深度审查
  ↓
【不通过】→ 智能修订指导 → 针对性修订 → 重新检查
  ↓
【通过】→ 更新记忆库 → 检查点一致性检查
  ↓
保存并提交
```

## 配置选项

新增配置项（`config.yaml`）：

```yaml
writing:
  use_ai_review: true           # 是否使用AI深度审查
  use_deep_consistency_check: true  # 是否启用跨章节一致性检查
  max_revisions: 3              # 最大修订次数

review:
  checkpoint:
    per_chapter: true
    minor_check_interval: 10
    major_check_interval: 50
  min_score_threshold: 7        # 最低分数阈值

memory:
  enabled: true
  foreshadow_overdue_warning: 30   # 伏笔超期警告
  foreshadow_overdue_critical: 50  # 伏笔超期严重
```

## 预期效果

| 问题类型 | 改进前 | 改进后 |
|----------|--------|--------|
| POV越界 | 几乎无法检测 | AI语义分析检测 |
| 人物OOC | 无法检测 | 对比人物档案检测 |
| 伏笔遗忘 | 无法追踪 | 记忆库追踪+超期提醒 |
| 时间线矛盾 | 无检查 | 时间线索引检查 |
| 跨章节矛盾 | 只看前3章 | 全局记忆+检查点 |
| 修订效率 | 盲目重写 | 针对性指导修订 |

## 使用方式

```python
# 初始化增强版Writer
writer = Writer(project_path, config)

# 写作单章（自动启用所有增强功能）
result = writer.run(chapter_num=1)

# 批量写作
result = writer.run_batch(count=50)

# 手动触发一致性检查
checker = ConsistencyChecker(project_path, config)
result = checker.major_check(chapter_num=50)
```

## 注意事项

1. **API成本**：AI深度审查会增加API调用次数，建议在关键章节启用
2. **检查频率**：可根据需要调整检查点间隔
3. **记忆库维护**：记忆库会持续增长，建议定期清理不活跃的追踪项
4. **降级策略**：当AI审查失败时，系统会自动回退到规则基础检查

---

*此改进方案旨在解决"完全无人监管可能导致质量参差或逻辑矛盾"的问题，通过多层质量保障机制确保长篇小说的一致性和质量。*
