"""
LLM接口模块，提供与现有系统集成的标注功能
"""
from typing import Union, List, Dict, Any
from .knowledge_slice_annotator import KnowledgeSliceAnnotator
import json

class LLMAnnotationInterface:
    """
    LLM标注接口类，用于与现有系统集成
    """
    
    def __init__(self):
        self.annotators = {}  # 缓存不同领域的标注器
    
    def get_or_create_annotator(self, domain_config: dict, questions_config: dict) -> KnowledgeSliceAnnotator:
        """
        获取或创建标注器实例
        
        Args:
            domain_config: 领域配置
            questions_config: 问题库配置
            
        Returns:
            KnowledgeSliceAnnotator实例
        """
        # 创建缓存键
        cache_key = f"{domain_config.get('knowledge_domain', '')}_{hash(json.dumps(questions_config, sort_keys=True))}"
        
        if cache_key not in self.annotators:
            self.annotators[cache_key] = KnowledgeSliceAnnotator(domain_config, questions_config)
        
        return self.annotators[cache_key]
    
    def annotate_single_slice(self, domain_config: dict, questions_config: dict, slice_text: str) -> Union[Dict[str, List[int]], str]:
        """
        标注单个知识切片
        
        Args:
            domain_config: 领域配置
            questions_config: 问题库配置
            slice_text: 知识切片文本
            
        Returns:
            标注结果
        """
        annotator = self.get_or_create_annotator(domain_config, questions_config)
        return annotator.analyze_slice(slice_text)
    

# 创建全局接口实例
llm_annotation_interface = LLMAnnotationInterface()



