"""
LLM模块初始化文件
"""
from src.llm.knowledge_slice_annotator import KnowledgeSliceAnnotator
from src.llm.llm_interface import (
    LLMAnnotationInterface,
    llm_annotation_interface
)

__all__ = [
    'KnowledgeSliceAnnotator',
    'LLMAnnotationInterface',
    'llm_annotation_interface'
]