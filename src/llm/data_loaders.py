import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from datasets import load_from_disk

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.utils.pub_funs import read_json_file


# ==================== 数据模型 ====================

@dataclass
class QuestionAnswerPair:
    """问答对数据结构"""
    id: str
    question: str
    context: str
    answers: List[str]  # 标准答案列表
    metadata: Dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> 'QuestionAnswerPair':
        """从字典创建问答对"""
        # 处理不同格式的answers
        answers = data.get('answers', {})
        if isinstance(answers, dict):
            answer_texts = answers.get('text', [])
        elif isinstance(answers, list):
            answer_texts = answers
        else:
            answer_texts = [str(answers)]

        return cls(
            id=str(data.get('id', '')),
            question=data.get('question', ''),
            context=data.get('context', ''),
            answers=answer_texts,
            metadata={
                'title': data.get('title', ''),
                'answer_start': answers.get('answer_start', []) if isinstance(answers, dict) else []
            }
        )


@dataclass
class ModelResponse:
    """
    模型回答数据结构
    
    新增字段：
    - metrics: 单个问题的详细评估指标，包含以下子字段：
        - exact_match: 精确匹配率 (0.0-1.0)
        - f1_score: F1分数 (0.0-1.0)
        - semantic_similarity: 语义相似度 (0.0-1.0)
        - answer_coverage: 答案覆盖率 (0.0-1.0)
        - answer_relevance: 答案相关性 (0.0-1.0)
        - context_utilization: 上下文利用率 (0.0-1.0)
        - answer_completeness: 答案完整性 (0.0-1.0)
        - answer_conciseness: 答案简洁性 (0.0-1.0)
        - inference_time: 推理时间
        - success: 是否成功 (1.0或0.0)
    """
    question_id: str
    question: str
    context: str
    predicted_answer: str
    ground_truth: List[str]
    success: bool
    inference_time: float
    error_message: str = ""
    metadata: Dict = field(default_factory=dict)
    # 新增：单个问题的评估指标
    metrics: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class EvaluationMetrics:
    """评估指标数据结构"""
    # 基础指标
    total_samples: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0

    # 准确性指标
    exact_match: float = 0.0
    f1_score: float = 0.0

    # 语义相似度指标
    semantic_similarity: float = 0.0

    # 效率指标
    avg_inference_time: float = 0.0
    total_inference_time: float = 0.0

    # 知识库相关指标
    answer_coverage: float = 0.0  # 答案覆盖率
    answer_relevance: float = 0.0  # 答案相关性
    context_utilization: float = 0.0  # 上下文利用率

    # 质量指标
    answer_completeness: float = 0.0  # 答案完整性
    answer_conciseness: float = 0.0  # 答案简洁性

    # 时间戳
    evaluation_time: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class ModelEvaluationResult:
    """
    单个模型的评估结果
    
    新增字段：
    - question_metrics: 每个问题的详细指标字典
        格式: {question_id: {metric_name: value, ...}, ...}
    """
    model_name: str
    model_version: str
    model_config: Dict
    metrics: EvaluationMetrics
    responses: List[ModelResponse]
    evaluation_config: Dict = field(default_factory=dict)
    # 新增：每个问题的详细指标
    question_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'model_name': self.model_name,
            'model_version': self.model_version,
            'model_config': self.model_config,
            'metrics': self.metrics.to_dict(),
            'responses': [r.to_dict() for r in self.responses],
            'evaluation_config': self.evaluation_config,
            'question_metrics': self.question_metrics
        }

    def get_metric_distribution(self, metric: str) -> Dict[str, float]:
        """
        获取指定指标的分布统计
        
        Args:
            metric: 指标名称
            
        Returns:
            包含min, max, mean, median, std的字典
        """
        import numpy as np
        
        values = [
            m.get(metric, 0.0) 
            for m in self.question_metrics.values() 
            if metric in m
        ]
        
        if not values:
            return {'min': 0.0, 'max': 0.0, 'mean': 0.0, 'median': 0.0, 'std': 0.0}
        
        arr = np.array(values)
        return {
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'mean': float(np.mean(arr)),
            'median': float(np.median(arr)),
            'std': float(np.std(arr))
        }

    def get_questions_by_metric(
        self, 
        metric: str = 'f1_score',
        sort_order: str = 'desc',
        limit: int = None
    ) -> List[Dict]:
        """
        根据指定指标获取问题列表
        
        Args:
            metric: 指标名称
            sort_order: 排序方式 'asc'升序或'desc'降序
            limit: 返回数量限制
            
        Returns:
            问题列表，每个元素包含question_id和指标值
        """
        items = []
        for qid, metrics in self.question_metrics.items():
            if metric in metrics:
                # 获取对应的响应以补充信息
                response = next(
                    (r for r in self.responses if str(r.question_id) == str(qid)), 
                    None
                )
                items.append({
                    'question_id': qid,
                    'metric_value': metrics[metric],
                    'question': response.question if response else '',
                    'predicted_answer': response.predicted_answer if response else '',
                    'ground_truth': response.ground_truth if response else [],
                    'all_metrics': metrics
                })
        
        # 排序
        reverse = sort_order == 'desc'
        items.sort(key=lambda x: x['metric_value'], reverse=reverse)
        
        if limit:
            items = items[:limit]
        
        return items

    def get_best_worst_questions(
        self, 
        metric: str = 'f1_score',
        top_n: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        获取最佳和最差表现的问题
        
        Args:
            metric: 用于排序的指标名称
            top_n: 返回的问题数量
            
        Returns:
            {
                "best": [{question_id, question, metric_value, ...}, ...],
                "worst": [{...}, ...]
            }
        """
        sorted_items = self.get_questions_by_metric(metric, sort_order='desc')
        
        return {
            'best': sorted_items[:top_n],
            'worst': sorted_items[-top_n:][::-1]  # 倒序，最差的是最后一个
        }


# ==================== 数据集加载器 ====================

class DatasetLoader:
    """问答对数据集加载器"""

    @staticmethod
    def load_from_hf_dataset(dataset_path: str, split: str = 'test') -> List[QuestionAnswerPair]:
        """
        从HuggingFace数据集格式加载

        Args:
            dataset_path: 数据集路径
            split: 数据集分割 (test/validation/train)

        Returns:
            问答对列表
        """
        try:
            dataset = load_from_disk(dataset_path)

            if split in dataset:
                data_split = dataset[split]
            else:
                logger.warning(f"分割 {split} 不存在，使用第一个可用分割")
                data_split = dataset[list(dataset.keys())[0]]

            qa_pairs = []
            for item in data_split:
                qa_pairs.append(QuestionAnswerPair.from_dict(item))

            logger.info(f"成功加载 {len(qa_pairs)} 个问答对 (来自 {split} 分割)")
            return qa_pairs

        except ImportError:
            logger.error("未安装datasets库，请运行: pip install datasets")
            raise
        except Exception as e:
            logger.error(f"加载数据集失败: {e}")
            raise

    @staticmethod
    def load_from_json(json_path: str) -> List[QuestionAnswerPair]:
        """
        从JSON文件加载

        Args:
            json_path: JSON文件路径

        Returns:
            问答对列表
        """
        data = read_json_file(json_path, default=[])

        # 支持两种格式：列表或包含data字段的字典
        if isinstance(data, dict):
            qa_data = data.get('data', data.get('qa_pairs', []))
        else:
            qa_data = data

        qa_pairs = [QuestionAnswerPair.from_dict(item) for item in qa_data]
        logger.info(f"成功加载 {len(qa_pairs)} 个问答对 (来自 {json_path})")
        return qa_pairs

    @staticmethod
    def load_from_jsonl(jsonl_path: str) -> List[QuestionAnswerPair]:
        """
        从JSONL文件加载

        Args:
            jsonl_path: JSONL文件路径

        Returns:
            问答对列表
        """
        qa_pairs = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    qa_pairs.append(QuestionAnswerPair.from_dict(item))

        logger.info(f"成功加载 {len(qa_pairs)} 个问答对 (来自 {jsonl_path})")
        return qa_pairs
