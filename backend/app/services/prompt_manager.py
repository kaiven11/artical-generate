"""
Enhanced prompt management service for AI detection evasion.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import random

from ..models.prompt import PromptTemplate, PromptType
from ..core.database import get_db_session, get_db_connection


class OptimizationLevel(str, Enum):
    """Optimization levels based on AI detection results."""
    LIGHT = "light"      # AI probability < 25%
    STANDARD = "standard"  # AI probability 25-50%
    HEAVY = "heavy"      # AI probability > 50%


class ContentType(str, Enum):
    """Content types for differentiated processing."""
    TECHNICAL = "technical"
    NEWS = "news"
    TUTORIAL = "tutorial"
    GENERAL = "general"


class PromptManager:
    """Enhanced prompt management service for AI detection evasion."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._templates_cache = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load prompt templates from database."""
        try:
            # Use direct database connection for synchronous loading
            from ..core.database import get_db_connection
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM prompt_templates WHERE is_active = 1")
                rows = cursor.fetchall()

                for row in rows:
                    key = f"{row['type']}_{row['name']}"
                    # Create a simple template object
                    template = type('PromptTemplate', (), {
                        'id': row['id'],
                        'name': row['name'],
                        'type': row['type'],
                        'template': row['template'],
                        'is_active': row['is_active']
                    })()
                    self._templates_cache[key] = template

                self.logger.info(f"Loaded {len(rows)} prompt templates")
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
    
    def get_optimization_prompt(
        self,
        content: str,
        ai_probability: float,
        round_number: int = 1,
        content_type: ContentType = ContentType.GENERAL,
        detection_feedback: str = "",
        platform: str = "toutiao"
    ) -> str:
        """
        Get optimized prompt based on AI detection results and context.

        Args:
            content: Content to optimize
            ai_probability: Current AI detection probability
            round_number: Optimization round number
            content_type: Type of content
            detection_feedback: Feedback from AI detection
            platform: Target platform

        Returns:
            Optimized prompt string
        """
        # Determine optimization level
        if ai_probability > 50:
            level = OptimizationLevel.HEAVY
        elif ai_probability > 25:
            level = OptimizationLevel.STANDARD
        else:
            level = OptimizationLevel.LIGHT

        self.logger.info(f"🎯 选择优化级别: {level.value} (AI概率: {ai_probability}%, 轮次: {round_number})")

        # Try to get prompt template from database first
        template = self.get_template_by_criteria(
            template_type=PromptType.OPTIMIZATION,
            optimization_level=level,
            content_type=content_type
        )

        if template:
            self.logger.info(f"📚 使用数据库提示词模板: {template.name}")
            # Use template from database and fill variables
            prompt = self._fill_template_variables(
                template=template,
                variables={
                    'content': content,
                    'objective': self._get_optimization_objective(level, round_number),
                    'level_requirements': self._get_level_requirements_text(level),
                    'platform': platform,
                    'detection_feedback': detection_feedback if detection_feedback else "无特殊反馈"
                }
            )
        else:
            self.logger.info("📝 数据库中未找到合适模板，使用动态构建提示词")
            # Fallback to dynamic prompt building
            prompt = self._build_dynamic_prompt(
                content=content,
                level=level,
                round_number=round_number,
                content_type=content_type,
                detection_feedback=detection_feedback,
                platform=platform
            )

        return prompt
    
    def _build_dynamic_prompt(
        self,
        content: str,
        level: OptimizationLevel,
        round_number: int,
        content_type: ContentType,
        detection_feedback: str,
        platform: str
    ) -> str:
        """Build dynamic prompt based on parameters."""
        
        # Base role and objective
        role = self._get_role_definition(content_type)
        objective = self._get_optimization_objective(level, round_number)
        requirements = self._get_optimization_requirements(level, content_type, platform)
        
        # Build prompt
        prompt_parts = [
            f"你是{role}。",
            "",
            f"优化目标：{objective}",
            "",
            "具体要求：",
        ]
        
        # Add requirements
        for i, req in enumerate(requirements, 1):
            prompt_parts.append(f"{i}. {req}")
        
        # Add detection feedback if available
        if detection_feedback:
            prompt_parts.extend([
                "",
                f"检测反馈：{detection_feedback}",
            ])
        
        # Add content and output instruction
        prompt_parts.extend([
            "",
            "原文内容：",
            content,
            "",
            "请直接输出优化后的内容，不要添加任何解释或说明。"
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_role_definition(self, content_type: ContentType) -> str:
        """Get role definition based on content type."""
        roles = {
            ContentType.TECHNICAL: "一位资深的技术内容创作者，具有丰富的技术写作经验和深厚的行业背景",
            ContentType.NEWS: "一位经验丰富的新闻编辑，擅长将信息转化为引人入胜的新闻报道",
            ContentType.TUTORIAL: "一位专业的教育内容创作者，善于将复杂概念转化为易懂的教程",
            ContentType.GENERAL: "一位专业的内容创作专家，具有多年的写作和编辑经验"
        }
        return roles.get(content_type, roles[ContentType.GENERAL])
    
    def _get_optimization_objective(self, level: OptimizationLevel, round_number: int) -> str:
        """Get optimization objective based on level and round."""
        base_objectives = {
            OptimizationLevel.LIGHT: "对内容进行轻度优化，提升自然度和可读性",
            OptimizationLevel.STANDARD: "对内容进行中度改写，显著降低AI痕迹",
            OptimizationLevel.HEAVY: "对内容进行深度重构，彻底消除AI生成特征"
        }
        
        base = base_objectives[level]
        
        if round_number > 1:
            base += f"（第{round_number}轮优化，需要更加彻底的改写）"
        
        return base

    def _get_optimization_requirements(
        self,
        level: OptimizationLevel,
        content_type: ContentType,
        platform: str
    ) -> List[str]:
        """Get optimization requirements based on level, content type and platform."""

        # Base requirements for all levels
        base_requirements = [
            "保持原文的核心观点和关键信息完整性",
            "确保内容的逻辑结构清晰合理"
        ]

        # Level-specific requirements
        level_requirements = {
            OptimizationLevel.LIGHT: [
                "调整部分句式结构，增加表达的自然性",
                "适当添加一些个人化的表达方式",
                "保持原文的整体风格和语调"
            ],
            OptimizationLevel.STANDARD: [
                "显著改变句式结构和表达方式",
                "增加更多个人化的见解和评论",
                "调整段落组织，使其更符合人类写作习惯",
                "添加适当的口语化表达和语气词"
            ],
            OptimizationLevel.HEAVY: [
                "彻底重构文章的表达方式和语言风格",
                "大量增加个人化的观点、经验和感受",
                "完全改变句式模式，避免AI写作的规整性",
                "添加丰富的情感色彩和主观判断",
                "模拟真实的人类思维过程和表达习惯",
                "增加不规则的语言特征和个性化表达"
            ]
        }

        # Content type specific requirements
        content_requirements = {
            ContentType.TECHNICAL: [
                "保持技术术语的准确性和专业性",
                "添加个人的技术见解和实践经验",
                "适当分享相关的技术背景和应用场景"
            ],
            ContentType.NEWS: [
                "增加新闻评论和个人观点",
                "添加对事件的分析和预测",
                "融入时事背景和相关联想"
            ],
            ContentType.TUTORIAL: [
                "增加个人的学习心得和实践建议",
                "添加常见问题和解决方案的分享",
                "融入教学经验和学习技巧"
            ],
            ContentType.GENERAL: [
                "增加个人的生活感悟和经验分享",
                "添加相关的联想和思考过程"
            ]
        }

        # Platform specific requirements
        platform_requirements = {
            "toutiao": [
                "标题要有吸引力，内容要有话题性",
                "适合大众阅读，语言通俗易懂",
                "增加互动性和争议性元素"
            ],
            "weixin": [
                "内容要有价值，适合分享传播",
                "语言要精准，逻辑要清晰",
                "增加实用性和可操作性"
            ],
            "zhihu": [
                "内容要专业深入，有知识价值",
                "逻辑要严密，论证要充分",
                "增加专业性和权威性"
            ]
        }

        # Combine all requirements
        requirements = base_requirements.copy()
        requirements.extend(level_requirements.get(level, []))
        requirements.extend(content_requirements.get(content_type, []))
        requirements.extend(platform_requirements.get(platform, []))

        return requirements

    def get_translation_prompt(
        self,
        content: str,
        source_lang: str = "en",
        target_lang: str = "zh",
        content_type: ContentType = ContentType.GENERAL,
        title: str = ""
    ) -> str:
        """Get translation prompt with humanization features."""

        role = self._get_role_definition(content_type)

        # Language mapping
        lang_names = {
            "en": "英文",
            "zh": "中文",
            "ja": "日文",
            "ko": "韩文"
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        prompt_parts = [
            f"你是{role}，同时也是一位专业的翻译专家。",
            "",
            f"请将以下{source_name}内容翻译成{target_name}，要求：",
            "",
            "1. 保持原文的核心观点和信息完整性",
            "2. 使用自然流畅的中文表达，避免翻译腔",
            "3. 适当调整句式以符合中文阅读习惯",
            "4. 保留专业术语的准确性",
            "5. 增加适当的本土化表达，使其更符合中文语境",
            "6. 保持段落结构，但可以适当调整句子组织",
            ""
        ]

        if title:
            prompt_parts.extend([
                f"文章标题：{title}",
                ""
            ])

        prompt_parts.extend([
            "原文内容：",
            content,
            "",
            "请直接输出翻译结果，不要添加任何解释或说明。"
        ])

        return "\n".join(prompt_parts)

    def create_enhanced_templates(self) -> List[PromptTemplate]:
        """Create enhanced prompt templates for AI detection evasion."""

        templates = []

        # Basic optimization template
        basic_optimization = PromptTemplate()
        basic_optimization.name = "basic_humanization_v2"
        basic_optimization.display_name = "基础人性化优化模板 v2.0"
        basic_optimization.description = "基础的内容人性化优化，适用于轻度AI痕迹降低"
        basic_optimization.template = """你是一位专业的内容创作专家，具有多年的写作和编辑经验。

优化目标：对内容进行轻度优化，提升自然度和可读性

具体要求：
1. 保持原文的核心观点和关键信息完整性
2. 确保内容的逻辑结构清晰合理
3. 调整部分句式结构，增加表达的自然性
4. 适当添加一些个人化的表达方式
5. 保持原文的整体风格和语调

原文内容：
{content}

请直接输出优化后的内容，不要添加任何解释或说明。"""
        basic_optimization.type = PromptType.OPTIMIZATION
        basic_optimization.variables = ["content"]
        basic_optimization.is_active = True
        basic_optimization.priority = 5
        templates.append(basic_optimization)

        # AI trace reduction template
        ai_reduction = PromptTemplate()
        ai_reduction.name = "ai_trace_reduction_v2"
        ai_reduction.display_name = "AI痕迹深度降低模板 v2.0"
        ai_reduction.description = "专门用于降低AI检测浓度的深度优化模板"
        ai_reduction.template = """你是一位资深的内容创作者，具有丰富的写作经验和深厚的行业背景。

优化目标：对内容进行深度重构，彻底消除AI生成特征

具体要求：
1. 保持原文的核心观点和关键信息完整性
2. 彻底重构文章的表达方式和语言风格
3. 大量增加个人化的观点、经验和感受
4. 完全改变句式模式，避免AI写作的规整性
5. 添加丰富的情感色彩和主观判断
6. 模拟真实的人类思维过程和表达习惯
7. 增加不规则的语言特征和个性化表达
8. 适当添加口语化表达和语气词

{detection_feedback}

原文内容：
{content}

请直接输出优化后的内容，不要添加任何解释或说明。"""
        ai_reduction.type = PromptType.OPTIMIZATION
        ai_reduction.variables = ["content", "detection_feedback"]
        ai_reduction.is_active = True
        ai_reduction.priority = 10
        templates.append(ai_reduction)

        # Technical content optimization
        technical_optimization = PromptTemplate()
        technical_optimization.name = "technical_humanization_v2"
        technical_optimization.display_name = "技术内容人性化模板 v2.0"
        technical_optimization.description = "专门用于技术文章的人性化优化"
        technical_optimization.template = """你是一位资深的技术内容创作者，具有丰富的技术写作经验和深厚的行业背景。

优化目标：{objective}

具体要求：
1. 保持原文的核心观点和关键信息完整性
2. 保持技术术语的准确性和专业性
3. 添加个人的技术见解和实践经验
4. 适当分享相关的技术背景和应用场景
5. {level_requirements}
6. 确保内容适合{platform}平台发布

{detection_feedback}

原文内容：
{content}

请直接输出优化后的内容，不要添加任何解释或说明。"""
        technical_optimization.type = PromptType.OPTIMIZATION
        technical_optimization.variables = ["content", "objective", "level_requirements", "platform", "detection_feedback"]
        technical_optimization.is_active = True
        technical_optimization.priority = 8
        templates.append(technical_optimization)

        return templates

    def save_templates_to_db(self, templates: List[PromptTemplate]):
        """Save templates to database."""
        try:
            with get_db_session() as session:
                for template in templates:
                    # Check if template already exists
                    existing = session.query(PromptTemplate).filter(
                        PromptTemplate.name == template.name
                    ).first()

                    if existing:
                        # Update existing template
                        for attr in ['display_name', 'description', 'template', 'variables', 'priority']:
                            setattr(existing, attr, getattr(template, attr))
                        existing.updated_at = datetime.utcnow()
                        self.logger.info(f"Updated template: {template.name}")
                    else:
                        # Add new template
                        session.add(template)
                        self.logger.info(f"Added new template: {template.name}")

                session.commit()
                self.logger.info(f"Successfully saved {len(templates)} templates")

                # Reload cache
                self._load_templates()

        except Exception as e:
            self.logger.error(f"Failed to save templates: {e}")
            raise

    def get_template_by_criteria(
        self,
        template_type: PromptType,
        optimization_level: OptimizationLevel = None,
        content_type: ContentType = None
    ) -> Optional[PromptTemplate]:
        """Get template by specific criteria."""

        # Define template selection logic
        template_mapping = {
            (PromptType.OPTIMIZATION, OptimizationLevel.LIGHT): "basic_humanization_v2",
            (PromptType.OPTIMIZATION, OptimizationLevel.STANDARD): "ai_trace_reduction_v2",
            (PromptType.OPTIMIZATION, OptimizationLevel.HEAVY): "ai_trace_reduction_v2",
        }

        # Special handling for technical content
        if content_type == ContentType.TECHNICAL:
            template_name = "technical_humanization_v2"
        else:
            key = (template_type, optimization_level)
            template_name = template_mapping.get(key)

        if template_name:
            template_key = f"{template_type}_{template_name}"
            return self._templates_cache.get(template_key)

        return None

    def _fill_template_variables(self, template, variables: Dict[str, str]) -> str:
        """Fill template variables with provided values."""
        try:
            # Get template content
            template_content = template.template

            # Replace variables in template
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                template_content = template_content.replace(placeholder, str(var_value))

            self.logger.info(f"✅ 模板变量填充完成，共替换 {len(variables)} 个变量")
            return template_content

        except Exception as e:
            self.logger.error(f"❌ 模板变量填充失败: {e}")
            # Return original template if variable filling fails
            return template.template

    def _get_level_requirements_text(self, level: OptimizationLevel) -> str:
        """Get level requirements as formatted text."""
        level_requirements = {
            OptimizationLevel.LIGHT: [
                "调整部分句式结构，增加表达的自然性",
                "适当添加一些个人化的表达方式",
                "保持原文的整体风格和语调"
            ],
            OptimizationLevel.STANDARD: [
                "显著改变句式结构和表达方式",
                "增加更多个人化的见解和评论",
                "调整段落组织，使其更符合人类写作习惯",
                "添加适当的口语化表达和语气词"
            ],
            OptimizationLevel.HEAVY: [
                "彻底重构文章的表达方式和语言风格",
                "大量增加个人化的观点、经验和感受",
                "完全改变句式模式，避免AI写作的规整性",
                "添加丰富的情感色彩和主观判断",
                "模拟真实的人类思维过程和表达习惯",
                "增加不规则的语言特征和个性化表达"
            ]
        }

        requirements = level_requirements.get(level, [])
        return "; ".join(requirements)


# Service instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
