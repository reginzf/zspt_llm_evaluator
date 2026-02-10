"""
LLM模块初始化文件
统一导出LLM相关的所有类和函数
"""

# 评估系统核心组件
from .api_agent_evaluator import (
    LLMEvaluator,
    run_evaluation,
    MetricsCalculator,
    # 数据模型
    QuestionAnswerPair,
    ModelResponse,
    EvaluationMetrics,
    ModelEvaluationResult,
    # 数据加载器
    DatasetLoader
)

# 基础Agent框架
from .llm_agent_basic import (
    BaseLLMAgent,
    DeepSeekAgent,
    create_agent
)

# 配置管理
from .config_manager import ConfigManager

# 知识切片标注
from .knowledge_slice_annotator import KnowledgeSliceAnnotator

# LLM接口
from .llm_interface import (
    LLMAnnotationInterface,
    llm_annotation_interface
)


__all__ = [
    # 评估系统核心
    'LLMEvaluator',
    'run_evaluation',
    'MetricsCalculator',
    
    # 数据模型
    'QuestionAnswerPair',
    'ModelResponse', 
    'EvaluationMetrics',
    'ModelEvaluationResult',
    
    # 数据加载器
    'DatasetLoader',
    
    # Agent框架
    'BaseLLMAgent',
    'DeepSeekAgent',
    'create_agent',
    
    # 配置管理
    'ConfigManager',
    
    # 知识切片标注
    'KnowledgeSliceAnnotator',
    
    # LLM接口
    'LLMAnnotationInterface',
    'llm_annotation_interface'
]