# LLM参数配置优化说明

## 问题描述

用户提出了三个重要问题：

1. **LLM API参数硬编码**：
   ```python
   "temperature": 0.7,
   "max_tokens": 4000,
   "top_p": 1,
   "frequency_penalty": 0,
   "presence_penalty": 0
   ```
   这些参数都是硬编码的，无法根据需求调整

2. **目标长度未传递给提示词**：
   - 页面选择的文章目标长度（如300-500字）没有加入到提示词中
   - 导致生成的文章长度不符合用户期望

3. **日志显示不完整**：
   - 发送给大模型的文本只显示前500字符
   - 无法查看完整的提示词内容，不利于调试

## 解决方案

### 1. LLM API参数可配置化

**位置**：`backend/app/services/llm_api.py`

**修改内容**：

#### A. 修改_call_api方法支持动态参数

```python
async def _call_api(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
    """Call the LLM API with improved error handling and configurable parameters."""
    
    # 可配置的API参数，支持通过kwargs传递
    payload = {
        "model": model or self.default_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": kwargs.get('temperature', 0.7),
        "max_tokens": kwargs.get('max_tokens', 4000),
        "top_p": kwargs.get('top_p', 1.0),
        "frequency_penalty": kwargs.get('frequency_penalty', 0.0),
        "presence_penalty": kwargs.get('presence_penalty', 0.0)
    }
```

#### B. 详细的参数日志

```python
self.logger.info(f"📊 请求参数:")
self.logger.info(f"   🌡️  温度: {payload['temperature']}")
self.logger.info(f"   📏 最大tokens: {payload['max_tokens']}")
self.logger.info(f"   🎯 top_p: {payload['top_p']}")
self.logger.info(f"   🔄 frequency_penalty: {payload['frequency_penalty']}")
self.logger.info(f"   👥 presence_penalty: {payload['presence_penalty']}")
```

### 2. 目标长度功能集成

**位置**：`backend/app/services/llm_api.py`

**修改内容**：

#### A. 添加target_length参数

```python
async def create_content_by_topic(
    self, 
    topic: str, 
    keywords: List[str] = None, 
    requirements: str = "", 
    custom_prompt: str = "",
    model: str = None,
    target_length: str = "medium",  # 新增参数
    **api_params  # 支持API参数传递
) -> LLMResponse:
```

#### B. 长度映射和处理逻辑

```python
# 定义目标长度映射
length_mapping = {
    "mini": {"words": "300-500", "description": "简短文章"},
    "short": {"words": "500-800", "description": "短篇文章"},
    "medium": {"words": "800-1500", "description": "中等长度文章"},
    "long": {"words": "1500-3000", "description": "长篇文章"}
}

length_info = length_mapping.get(target_length, length_mapping["medium"])
```

#### C. 自定义提示词长度处理

```python
if custom_prompt:
    # 检查是否包含长度变量占位符
    if "{target_length}" in custom_prompt:
        prompt = custom_prompt.format(target_length=length_info['words'])
    elif "字数" not in custom_prompt and "长度" not in custom_prompt:
        # 如果自定义提示词没有长度要求，添加长度指导
        prompt = custom_prompt + f"\n\n**字数要求：** 请控制文章字数在 {length_info['words']} 字之间。"
```

### 3. 全量文本日志显示

**位置**：`backend/app/services/llm_api.py`

**修改内容**：

```python
# 全量显示发送给API的提示词内容
self.logger.info("📤 发送给LLM的完整提示词内容:")
self.logger.info("=" * 80)
self.logger.info(prompt)  # 完整内容，不截断
self.logger.info("=" * 80)
```

**效果**：
- 完整显示发送给LLM的所有内容
- 使用明显的分隔线便于识别
- 方便调试和问题排查

### 4. 数据库模型配置支持

**位置**：`backend/app/services/article_processor.py`

**修改内容**：

```python
# 获取API参数配置（如果有的话）
api_params = {}
if hasattr(article, 'selected_model_id') and article.selected_model_id:
    # 从数据库获取模型配置
    cursor.execute("""
        SELECT temperature, max_tokens, top_p, frequency_penalty, presence_penalty
        FROM api_models WHERE id = ?
    """, (article.selected_model_id,))
    model_config = cursor.fetchone()
    
    if model_config:
        api_params = {
            'temperature': model_config[0] or 0.7,
            'max_tokens': model_config[1] or 4000,
            'top_p': model_config[2] or 1.0,
            'frequency_penalty': model_config[3] or 0.0,
            'presence_penalty': model_config[4] or 0.0
        }
```

### 5. 角色定位模板长度处理

**位置**：`backend/app/services/article_processor.py`

**修改内容**：

```python
# 在模板末尾添加明确的创作指令，包含目标长度
length_mapping = {
    "mini": "300-500",
    "short": "500-800", 
    "medium": "800-1500",
    "long": "1500-3000"
}

target_length = getattr(self, '_current_target_length', 'medium')
word_count = length_mapping.get(target_length, "800-1500")

creation_instruction = f"""
**📝 本次创作任务：**
请根据以上角色定位和写作要求，围绕主题"{topic}"创作一篇文章。

主题：{topic}
关键词：{keywords_str}
创作要求：{requirements or '请创作一篇高质量的文章。'}
字数要求：{word_count} 字

请直接开始创作文章内容，不要再重复角色定位说明。文章应该：
1. 紧扣主题"{topic}"
2. 体现上述写作风格和结构特点
3. 内容原创且有深度
4. 字数严格控制在 {word_count} 字之间

现在请开始创作："""
```

## 优化效果

### 1. 参数配置灵活性

- ✅ **动态参数**：temperature、max_tokens等参数可通过kwargs传递
- ✅ **模型配置**：支持从数据库读取模型特定的参数
- ✅ **默认值保护**：未配置时使用合理的默认值

### 2. 目标长度精确控制

- ✅ **长度映射**：mini(300-500) / short(500-800) / medium(800-1500) / long(1500-3000)
- ✅ **提示词集成**：自动将字数要求添加到提示词中
- ✅ **自定义支持**：支持自定义提示词的长度处理

### 3. 调试能力提升

- ✅ **全量日志**：完整显示发送给LLM的提示词内容
- ✅ **参数详情**：详细记录所有API参数
- ✅ **长度信息**：记录目标长度和字数要求

### 4. 用户体验改善

- ✅ **所见即所得**：页面选择的长度直接影响生成结果
- ✅ **参数透明**：用户可以看到实际使用的参数
- ✅ **问题诊断**：完整日志便于问题排查

## 使用说明

### 1. 目标长度选择

在主题创作页面选择目标长度：
- **mini**：300-500字，适合简短介绍
- **short**：500-800字，适合快速阅读
- **medium**：800-1500字，适合深度分析
- **long**：1500-3000字，适合详细论述

### 2. 模型参数配置

通过数据库配置不同模型的参数：
```sql
UPDATE api_models SET 
    temperature = 0.8,
    max_tokens = 3000,
    top_p = 0.9
WHERE id = 1;
```

### 3. 自定义提示词长度

在提示词中使用长度变量：
```
请围绕主题创作文章，字数要求：{target_length}字
```

### 4. 日志查看

查看完整的LLM交互日志：
```
📤 发送给LLM的完整提示词内容:
================================================================================
[完整的提示词内容]
================================================================================
```

## 测试验证

### 测试脚本

创建了专门的测试脚本 `test_llm_parameters.py`：

1. **参数配置测试**：验证动态参数传递
2. **目标长度测试**：验证长度映射和提示词构建
3. **全量日志测试**：验证完整文本显示
4. **数据库配置测试**：验证模型参数读取

### 验证要点

- ✅ 参数正确传递给LLM API
- ✅ 目标长度正确转换为字数要求
- ✅ 提示词包含完整的长度信息
- ✅ 日志显示完整的提示词内容

## 后续优化建议

1. **参数预设**：提供常用的参数组合预设
2. **长度验证**：验证生成内容是否符合长度要求
3. **参数调优**：根据使用效果优化默认参数
4. **用户界面**：在前端提供参数配置界面

## 总结

这次优化解决了LLM API使用中的三个关键问题：

1. **参数可配置**：从硬编码改为动态配置，支持个性化调整
2. **长度精确控制**：目标长度直接影响生成结果，提高用户满意度
3. **调试能力增强**：全量日志显示，便于问题诊断和优化

这些改进大大提升了系统的灵活性、可控性和可维护性。
