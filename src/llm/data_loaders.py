import json
import logging
from typing import Dict, List
from dataclasses import dataclass, field, asdict
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from utils.pub_funs import read_json_file


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
    """模型回答数据结构"""
    question_id: str
    question: str
    context: str
    predicted_answer: str
    ground_truth: List[str]
    success: bool
    inference_time: float
    error_message: str = ""
    metadata: Dict = field(default_factory=dict)

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
    partial_match: float = 0.0

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
    """单个模型的评估结果"""
    model_name: str
    model_version: str
    model_config: Dict
    metrics: EvaluationMetrics
    responses: List[ModelResponse]
    evaluation_config: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'model_name': self.model_name,
            'model_version': self.model_version,
            'model_config': self.model_config,
            'metrics': self.metrics.to_dict(),
            'responses': [r.to_dict() for r in self.responses],
            'evaluation_config': self.evaluation_config
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
            from datasets import load_from_disk
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
