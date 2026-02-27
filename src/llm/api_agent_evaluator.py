"""
LLM 知识库问答评估系统

功能流程:
1. 加载问答对数据集
2. 加载LLM配置并测试连通性
3. 进行问答，收集回答，保存临时文件
4. 将预测答案与标准答案对比，计算各项指标
5. 加工结果，生成详细的性能报告
6. 保存结果到本地，支持跨模型、跨时间比较
"""

import time
import logging
from typing import Dict, List, Tuple,Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import re
from rouge import Rouge
import numpy as np
from tqdm import tqdm
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from difflib import SequenceMatcher
from env_config_init import settings
from src.llm.data_loaders import DatasetLoader, QuestionAnswerPair, ModelResponse, ModelEvaluationResult, \
    EvaluationMetrics
from src.llm.llm_agent_basic import BaseLLMAgent, create_agent

# 配置rouge
rouge = Rouge()
# 延迟初始化语义模型
_model = None


def get_sentence_transformer_model():
    """延迟初始化并获取SentenceTransformer模型"""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_path = Path(settings.MODEL_PATH).parent / 'paraphrase-multilingual-MiniLM-L12-v2'
            _model = SentenceTransformer(str(model_path))
            logging.info("SentenceTransformer模型初始化完成")
        except Exception as e:
            logging.warning(f"SentenceTransformer模型初始化失败: {e}")
            _model = None
    return _model


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.pub_funs import write_json_file, read_json_file, ensure_directory_exists
from .config_manager import ConfigManager


# ==================== 评估指标计算器 ====================

class MetricsCalculator:
    """评估指标计算器"""

    @staticmethod
    def normalize_text(text: str) -> str:
        """标准化文本（用于比较）"""
        # 转换为小写
        text = text.lower()
        # 移除标点符号
        text = re.sub(r'[^\w\s]', '', text)
        # 规范化空白
        text = ' '.join(text.split())
        return text.strip()

    @staticmethod
    def calculate_exact_match(prediction: str, ground_truth: List[str], match_type=None) -> bool:
        """
        计算精确匹配
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            match_type: 匹配类型 None(默认标准化), strict(严格匹配), fuzzy(模糊匹配), 
                       semantic(语义匹配), rouge(ROUGE匹配)
            
        Returns:
            是否匹配
        """

        def match_normalized(pred: str, truth: str) -> bool:
            return MetricsCalculator.normalize_text(pred) == MetricsCalculator.normalize_text(truth)
        
        def match_fuzzy(pred: str, truth: str) -> bool:
            """模糊匹配 - 允许一定的差异"""
            pred_norm = MetricsCalculator.normalize_text(pred)
            truth_norm = MetricsCalculator.normalize_text(truth)
            # 计算编辑距离相似度
            similarity = SequenceMatcher(None, pred_norm, truth_norm).ratio()
            return similarity >= 0.9  # 90%以上相似度认为匹配
        
        def match_semantic(pred: str, truth: str) -> bool:
            """语义匹配 - 使用语义相似度"""
            model = get_sentence_transformer_model()
            if model is not None:
                try:
                    pred_embedding = model.encode(pred)
                    truth_embedding = model.encode(truth)
                    similarity = np.dot(pred_embedding, truth_embedding) / (
                        np.linalg.norm(pred_embedding) * np.linalg.norm(truth_embedding)
                    )
                    return similarity >= 0.95  # 95%以上语义相似度认为匹配
                except Exception as e:
                    logger.warning(f"语义匹配计算失败: {e}")
            # 回退到标准化匹配
            return match_normalized(pred, truth)
        
        def match_rouge(pred: str, truth: str) -> bool:
            """ROUGE匹配 - 使用ROUGE-L分数"""
            try:
                scores = rouge.get_scores(pred, truth)
                rouge_l_f1 = scores[0]['rouge-l']['f']  # F1分数
                return rouge_l_f1 >= 0.9  # 90%以上ROUGE分数认为匹配
            except Exception as e:
                logger.warning(f"ROUGE匹配计算失败: {e}")
                return match_normalized(pred, truth)
        
        def match_tfidf(pred: str, truth: str) -> bool:
            """TF-IDF匹配 - 基于TF-IDF向量相似度"""
            try:
                vectorizer = TfidfVectorizer()
                tfidf_matrix = vectorizer.fit_transform([pred, truth])
                similarity = (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
                return similarity >= 0.9  # 90%以上相似度认为匹配
            except Exception as e:
                logger.warning(f"TF-IDF匹配计算失败: {e}")
                return match_normalized(pred, truth)
        
        def match_keyword(pred: str, truth: str) -> bool:
            """关键词匹配 - 基于关键词重叠"""
            pred_words = set(MetricsCalculator.normalize_text(pred).split())
            truth_words = set(MetricsCalculator.normalize_text(truth).split())
            
            if not pred_words or not truth_words:
                return pred_words == truth_words
            
            # 计算Jaccard相似度
            intersection = len(pred_words & truth_words)
            union = len(pred_words | truth_words)
            jaccard_sim = intersection / union if union > 0 else 0
            return jaccard_sim >= 0.9  # 90%以上重叠认为匹配
        
        # 根据匹配类型选择匹配函数
        if match_type == 'fuzzy':
            match_func = match_fuzzy
        elif match_type == 'semantic':
            match_func = match_semantic
        elif match_type == 'rouge':
            match_func = match_rouge
        elif match_type == 'tfidf':
            match_func = match_tfidf
        elif match_type == 'keyword':
            match_func = match_keyword
        else:
            match_func = match_normalized  # 默认使用标准化匹配
        
        # 对每个标准答案进行匹配检查
        for truth in ground_truth:
            if match_func(prediction, truth):
                return True
        return False

    @staticmethod
    def calculate_f1_score(prediction: str, ground_truth: List[str], cal_type=None) -> float:
        """
        计算F1分数
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            cal_type: 计算方式 None(默认词汇), rouge, semantic
            
        Returns:
            F1分数 (0-1)
        """

        def cal_word_based(pred_tokens, truth_tokens):
            """基于词汇的传统F1计算"""
            common_tokens = set(pred_tokens) & set(truth_tokens)
            if len(common_tokens) == 0:
                return 0.0
            precision = len(common_tokens) / len(pred_tokens) if pred_tokens else 0
            recall = len(common_tokens) / len(truth_tokens) if truth_tokens else 0
            if precision + recall == 0:
                return 0.0
            return 2 * precision * recall / (precision + recall)
        
        def cal_rouge_based(prediction: str, ground_truth: List[str]) -> float:
            """基于ROUGE的F1计算"""
            best_score = 0.0
            for truth in ground_truth:
                try:
                    scores = rouge.get_scores(prediction, truth)
                    rouge_f1 = scores[0]['rouge-l']['f']  # ROUGE-L F1分数
                    best_score = max(best_score, rouge_f1)
                except Exception as e:
                    logger.warning(f"ROUGE F1计算失败: {e}")
                    continue
            return best_score
        
        def cal_semantic_based(prediction: str, ground_truth: List[str]) -> float:
            """基于语义相似度的F1计算"""
            model = get_sentence_transformer_model()
            if model is not None:
                try:
                    pred_embedding = model.encode(prediction)
                    best_similarity = 0.0
                    for truth in ground_truth:
                        truth_embedding = model.encode(truth)
                        similarity = np.dot(pred_embedding, truth_embedding) / (
                            np.linalg.norm(pred_embedding) * np.linalg.norm(truth_embedding)
                        )
                        best_similarity = max(best_similarity, similarity)
                    return max(0.0, min(1.0, best_similarity))
                except Exception as e:
                    logger.warning(f"语义F1计算失败: {e}")
            
            # 回退到词汇级别计算
            pred_tokens = MetricsCalculator.normalize_text(prediction).split()
            best_f1 = 0.0
            for truth in ground_truth:
                truth_tokens = MetricsCalculator.normalize_text(truth).split()
                f1 = cal_word_based(pred_tokens, truth_tokens)
                best_f1 = max(best_f1, f1)
            return best_f1
        
        def cal_jaccard_based(prediction: str, ground_truth: List[str]) -> float:
            """基于Jaccard相似度的计算"""
            pred_words = set(MetricsCalculator.normalize_text(prediction).split())
            best_jaccard = 0.0
            
            for truth in ground_truth:
                truth_words = set(MetricsCalculator.normalize_text(truth).split())
                if len(pred_words) == 0 and len(truth_words) == 0:
                    return 1.0
                elif len(pred_words) == 0 or len(truth_words) == 0:
                    continue
                
                intersection = len(pred_words & truth_words)
                union = len(pred_words | truth_words)
                jaccard = intersection / union if union > 0 else 0
                best_jaccard = max(best_jaccard, jaccard)
            
            return best_jaccard
        
        # 根据计算类型选择计算方法
        if cal_type == 'rouge':
            return cal_rouge_based(prediction, ground_truth)
        elif cal_type == 'semantic':
            return cal_semantic_based(prediction, ground_truth)
        elif cal_type == 'jaccard':
            return cal_jaccard_based(prediction, ground_truth)
        else:
            # 默认使用词汇级别的传统计算
            pred_tokens = MetricsCalculator.normalize_text(prediction).split()
            best_f1 = 0.0
            
            for truth in ground_truth:
                truth_tokens = MetricsCalculator.normalize_text(truth).split()
                f1 = cal_word_based(pred_tokens, truth_tokens)
                best_f1 = max(best_f1, f1)
            
            return best_f1

    @staticmethod
    def calculate_partial_match(prediction: str, ground_truth: List[str], match_type=None) -> float:
        """
        计算部分匹配分数
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            match_type: 匹配类型 None(默认词汇重叠), semantic(语义), rouge(ROUGE), 
                       tfidf(TF-IDF), jaccard(Jaccard相似度)
            
        Returns:
            部分匹配分数 (0-1)
        """

        def match_word_overlap(prediction: str, ground_truth: List[str]) -> float:
            """词汇重叠匹配 - 原有方式"""
            pred_clean = MetricsCalculator.normalize_text(prediction)
            pred_tokens = set(pred_clean.split())

            if not pred_tokens:
                return 0.0

            best_score = 0.0
            for truth in ground_truth:
                truth_clean = MetricsCalculator.normalize_text(truth)
                truth_tokens = set(truth_clean.split())

                if not truth_tokens:
                    continue

                # 计算重叠token比例
                overlap = pred_tokens & truth_tokens
                score = len(overlap) / max(len(pred_tokens), len(truth_tokens))
                best_score = max(best_score, score)

            return best_score
        
        def match_semantic(prediction: str, ground_truth: List[str]) -> float:
            """语义相似度匹配"""
            model = get_sentence_transformer_model()
            if model is not None:
                try:
                    pred_embedding = model.encode(prediction)
                    best_similarity = 0.0
                    for truth in ground_truth:
                        truth_embedding = model.encode(truth)
                        similarity = np.dot(pred_embedding, truth_embedding) / (
                            np.linalg.norm(pred_embedding) * np.linalg.norm(truth_embedding)
                        )
                        best_similarity = max(best_similarity, similarity)
                    return max(0.0, min(1.0, best_similarity))
                except Exception as e:
                    logger.warning(f"语义部分匹配计算失败: {e}")
            
            # 回退到词汇重叠
            return match_word_overlap(prediction, ground_truth)
        
        def match_rouge(prediction: str, ground_truth: List[str]) -> float:
            """ROUGE匹配"""
            best_score = 0.0
            for truth in ground_truth:
                try:
                    scores = rouge.get_scores(prediction, truth)
                    rouge_l = scores[0]['rouge-l']['r']  # 召回率
                    best_score = max(best_score, rouge_l)
                except Exception as e:
                    logger.warning(f"ROUGE部分匹配计算失败: {e}")
                    continue
            return best_score
        
        def match_tfidf(prediction: str, ground_truth: List[str]) -> float:
            """TF-IDF匹配"""
            try:
                vectorizer = TfidfVectorizer()
                best_similarity = 0.0
                
                for truth in ground_truth:
                    tfidf_matrix = vectorizer.fit_transform([prediction, truth])
                    similarity = (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
                    best_similarity = max(best_similarity, similarity)
                
                return max(0.0, min(1.0, best_similarity))
            except Exception as e:
                logger.warning(f"TF-IDF部分匹配计算失败: {e}")
                return match_word_overlap(prediction, ground_truth)
        
        def match_jaccard(prediction: str, ground_truth: List[str]) -> float:
            """Jaccard相似度匹配"""
            pred_words = set(MetricsCalculator.normalize_text(prediction).split())
            best_jaccard = 0.0
            
            for truth in ground_truth:
                truth_words = set(MetricsCalculator.normalize_text(truth).split())
                if len(pred_words) == 0 and len(truth_words) == 0:
                    return 1.0
                elif len(pred_words) == 0 or len(truth_words) == 0:
                    continue
                
                intersection = len(pred_words & truth_words)
                union = len(pred_words | truth_words)
                jaccard = intersection / union if union > 0 else 0
                best_jaccard = max(best_jaccard, jaccard)
            
            return best_jaccard
        
        # 根据匹配类型选择计算方法
        if match_type == 'semantic':
            return match_semantic(prediction, ground_truth)
        elif match_type == 'rouge':
            return match_rouge(prediction, ground_truth)
        elif match_type == 'tfidf':
            return match_tfidf(prediction, ground_truth)
        elif match_type == 'jaccard':
            return match_jaccard(prediction, ground_truth)
        else:
            # 默认使用词汇重叠
            return match_word_overlap(prediction, ground_truth)

    @staticmethod
    def calculate_semantic_similarity(prediction: str, ground_truth: List[str], sim_type=None) -> float:
        """
        计算语义相似度
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            sim_type: 相似度类型 None(默认SentenceTransformer), bert(BERT), 
                     tfidf(TF-IDF), word2vec(Word2Vec), jaccard(Jaccard)
            
        Returns:
            语义相似度 (0-1)
        """

        def sim_sentence_transformer(prediction: str, ground_truth: List[str]) -> float:
            """基于SentenceTransformer的语义相似度计算"""
            model = get_sentence_transformer_model()
            if model is not None:
                try:
                    pred_embedding = model.encode(prediction)
                    best_similarity = 0.0
                    for truth in ground_truth:
                        truth_embedding = model.encode(truth)
                        # 计算余弦相似度
                        similarity = np.dot(pred_embedding, truth_embedding) / (
                                np.linalg.norm(pred_embedding) * np.linalg.norm(truth_embedding)
                        )
                        best_similarity = max(best_similarity, similarity)
                    return max(0.0, min(1.0, best_similarity))  # 确保在0-1范围内
                except Exception as e:
                    logger.warning(f"使用SentenceTransformer计算语义相似度失败: {e}")

            # 回退到基于词重叠的计算方法
            return sim_jaccard_based(prediction, ground_truth)
        
        def sim_bert_based(prediction: str, ground_truth: List[str]) -> float:
            """基于BERT的语义相似度计算"""
            try:
                from transformers import AutoTokenizer, AutoModel
                import torch
                
                tokenizer = AutoTokenizer.from_pretrained('bert-base-chinese')
                model = AutoModel.from_pretrained('bert-base-chinese')
                
                def get_bert_embedding(text):
                    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
                    with torch.no_grad():
                        outputs = model(**inputs)
                    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                
                pred_embedding = get_bert_embedding(prediction)
                best_similarity = 0.0
                
                for truth in ground_truth:
                    truth_embedding = get_bert_embedding(truth)
                    similarity = np.dot(pred_embedding, truth_embedding) / (
                        np.linalg.norm(pred_embedding) * np.linalg.norm(truth_embedding)
                    )
                    best_similarity = max(best_similarity, similarity)
                
                return max(0.0, min(1.0, best_similarity))
            except Exception as e:
                logger.warning(f"BERT语义相似度计算失败: {e}")
                return sim_sentence_transformer(prediction, ground_truth)
        
        def sim_tfidf_based(prediction: str, ground_truth: List[str]) -> float:
            """基于TF-IDF的语义相似度计算"""
            try:
                vectorizer = TfidfVectorizer()
                best_similarity = 0.0
                
                for truth in ground_truth:
                    tfidf_matrix = vectorizer.fit_transform([prediction, truth])
                    similarity = (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
                    best_similarity = max(best_similarity, similarity)
                
                return max(0.0, min(1.0, best_similarity))
            except Exception as e:
                logger.warning(f"TF-IDF语义相似度计算失败: {e}")
                return sim_jaccard_based(prediction, ground_truth)
        
        def sim_word2vec_based(prediction: str, ground_truth: List[str]) -> float:
            """基于Word2Vec的语义相似度计算"""
            try:
                # 注意：需要先安装gensim: pip install gensim
                import gensim
                from gensim.models import Word2Vec
                
                # 这里假设已有训练好的Word2Vec模型
                # 实际使用时需要加载具体的模型
                logger.warning("Word2Vec模型需要预先训练，暂时回退到其他方法")
                return sim_tfidf_based(prediction, ground_truth)
            except ImportError:
                logger.warning("gensim未安装，无法使用Word2Vec方法")
                return sim_tfidf_based(prediction, ground_truth)
            except Exception as e:
                logger.warning(f"Word2Vec语义相似度计算失败: {e}")
                return sim_jaccard_based(prediction, ground_truth)
        
        def sim_jaccard_based(prediction: str, ground_truth: List[str]) -> float:
            """基于Jaccard相似度的计算（作为后备方法）"""
            pred_words = set(MetricsCalculator.normalize_text(prediction).split())
            best_similarity = 0.0

            for truth in ground_truth:
                truth_words = set(MetricsCalculator.normalize_text(truth).split())

                if len(pred_words) == 0 and len(truth_words) == 0:
                    return 1.0
                elif len(pred_words) == 0 or len(truth_words) == 0:
                    continue

                # Jaccard相似度
                intersection = len(pred_words & truth_words)
                union = len(pred_words | truth_words)
                similarity = intersection / union if union > 0 else 0
                best_similarity = max(best_similarity, similarity)

            return best_similarity
        
        # 根据相似度类型选择计算方法
        if sim_type == 'bert':
            return sim_bert_based(prediction, ground_truth)
        elif sim_type == 'tfidf':
            return sim_tfidf_based(prediction, ground_truth)
        elif sim_type == 'word2vec':
            return sim_word2vec_based(prediction, ground_truth)
        elif sim_type == 'jaccard':
            return sim_jaccard_based(prediction, ground_truth)
        else:
            # 默认使用SentenceTransformer
            return sim_sentence_transformer(prediction, ground_truth)

    @staticmethod
    def calculate_answer_coverage(prediction: str, ground_truth: List[str], cal_type=None, weights: List[float] = None) -> float:
        """
        计算答案覆盖率（预测答案包含标准答案信息的程度）
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            cal_type: 计算方式 None，rouge，sentence，weighted
            weights: 权重列表，仅在 cal_type='weighted' 时使用，默认[0.5, 0.5]
        Returns:
            覆盖率 (0-1)
        """

        def cal_simple(prediction: str, ground_truth: List[str]):
            pred_words = set(MetricsCalculator.normalize_text(prediction).split())
            if not pred_words:
                return 0.0

            best_coverage = 0.0
            for truth in ground_truth:
                truth_words = set(MetricsCalculator.normalize_text(truth).split())
                if not truth_words:
                    continue
                covered = truth_words & pred_words
                coverage = len(covered) / len(truth_words)
                best_coverage = max(best_coverage, coverage)

            return best_coverage

        def cal_rouge(prediction: str, ground_truth: List[str]):
            best_score = 0.0
            for truth in ground_truth:
                scores = rouge.get_scores(prediction, truth)
                rouge_l = scores[0]['rouge-l']['r']  # 召回率
                best_score = max(best_score, rouge_l)
            return best_score

        def cal_sentence(prediction: str, ground_truth: List[str]) -> float:
            model = get_sentence_transformer_model()
            if model is None:
                return 0.0
            try:
                pred_embedding = model.encode(prediction)
                best_similarity = 0.0
                for truth in ground_truth:
                    truth_embedding = model.encode(truth)
                    similarity = np.dot(pred_embedding, truth_embedding) / (
                            np.linalg.norm(pred_embedding) * np.linalg.norm(truth_embedding)
                    )
                    best_similarity = max(best_similarity, similarity)
                return max(0.0, min(1.0, best_similarity))
            except Exception as e:
                logger.warning(f"使用SentenceTransformer计算覆盖率失败: {e}")
                return 0.0

        def cal_weighted(prediction: str, ground_truth: List[str], weights: List[float]) -> float:
            if len(weights) != 2 or sum(weights) != 1:
                raise ValueError("权重之和必须为1")
            rouge_score = cal_rouge(prediction, ground_truth)
            sentence_score = cal_sentence(prediction, ground_truth)
            weighted_score = (rouge_score * weights[0] + sentence_score * weights[1])
            return weighted_score

        if cal_type == 'rouge':
            return cal_rouge(prediction, ground_truth)
        elif cal_type == 'sentence':
            return cal_sentence(prediction, ground_truth)
        elif cal_type == 'weighted':
            # 使用传入的权重或默认值
            effective_weights = weights if weights is not None else [0.5, 0.5]
            return cal_weighted(prediction, ground_truth, effective_weights)
        else:
            return cal_simple(prediction, ground_truth)

    @staticmethod
    def calculate_answer_relevance(prediction: str, question: str, context: str, rel_type=None, weights: List[float] = None) -> float:
        """
        计算答案与问题的相关性
        
        Args:
            prediction: 预测答案
            question: 问题
            context: 上下文
            rel_type: 相关性计算类型 None(默认词汇重叠), semantic(语义), tfidf(TF-IDF), 
                     weighted(加权组合), rouge(ROUGE)
            weights: 权重列表，仅在 rel_type='weighted' 时使用，默认[0.4, 0.4, 0.2]
            
        Returns:
            相关性分数 (0-1)
        """

        def rel_word_overlap(prediction: str, question: str, context: str) -> float:
            """基于词汇重叠的相关性计算"""
            pred_words = set(MetricsCalculator.normalize_text(prediction).split())
            question_words = set(MetricsCalculator.normalize_text(question).split())
            context_words = set(MetricsCalculator.normalize_text(context).split())

            if not pred_words:
                return 0.0

            # 计算与问题的重叠
            question_overlap = len(pred_words & question_words) / len(pred_words) if pred_words else 0

            # 计算与上下文的重叠
            context_overlap = len(pred_words & context_words) / len(pred_words) if pred_words else 0

            # 加权组合
            relevance = 0.3 * question_overlap + 0.7 * context_overlap
            return min(1.0, relevance)
        
        def rel_semantic(prediction: str, question: str, context: str) -> float:
            """基于语义相似度的相关性计算"""
            model = get_sentence_transformer_model()
            if model is not None:
                try:
                    pred_embedding = model.encode(prediction)
                    question_embedding = model.encode(question)
                    context_embedding = model.encode(context)
                    
                    # 计算与问题的语义相似度
                    question_sim = np.dot(pred_embedding, question_embedding) / (
                        np.linalg.norm(pred_embedding) * np.linalg.norm(question_embedding)
                    )
                    
                    # 计算与上下文的语义相似度
                    context_sim = np.dot(pred_embedding, context_embedding) / (
                        np.linalg.norm(pred_embedding) * np.linalg.norm(context_embedding)
                    )
                    
                    # 加权组合
                    relevance = 0.3 * question_sim + 0.7 * context_sim
                    return max(0.0, min(1.0, relevance))
                except Exception as e:
                    logger.warning(f"语义相关性计算失败: {e}")
            
            # 回退到词汇重叠
            return rel_word_overlap(prediction, question, context)
        
        def rel_tfidf(prediction: str, question: str, context: str) -> float:
            """基于TF-IDF的相关性计算"""
            try:
                vectorizer = TfidfVectorizer()
                
                # 计算与问题的相关性
                question_matrix = vectorizer.fit_transform([prediction, question])
                question_sim = (question_matrix * question_matrix.T).toarray()[0, 1]
                
                # 计算与上下文的相关性
                context_matrix = vectorizer.fit_transform([prediction, context])
                context_sim = (context_matrix * context_matrix.T).toarray()[0, 1]
                
                # 加权组合
                relevance = 0.3 * question_sim + 0.7 * context_sim
                return max(0.0, min(1.0, relevance))
            except Exception as e:
                logger.warning(f"TF-IDF相关性计算失败: {e}")
                return rel_word_overlap(prediction, question, context)
        
        def rel_weighted(prediction: str, question: str, context: str, weights: List[float] = None) -> float:
            """加权组合多种相关性计算方法"""
            if weights is None:
                weights = [0.4, 0.4, 0.2]  # 词汇、语义、TF-IDF的权重
            
            if len(weights) != 3 or abs(sum(weights) - 1.0) > 1e-6:
                raise ValueError("权重必须是长度为3的列表，且和为1")
            
            word_score = rel_word_overlap(prediction, question, context)
            semantic_score = rel_semantic(prediction, question, context)
            tfidf_score = rel_tfidf(prediction, question, context)
            
            weighted_score = (word_score * weights[0] + 
                            semantic_score * weights[1] + 
                            tfidf_score * weights[2])
            return weighted_score
        
        def rel_rouge(prediction: str, question: str, context: str) -> float:
            """基于ROUGE的相关性计算"""
            try:
                # 计算与问题的ROUGE分数
                question_scores = rouge.get_scores(prediction, question)
                question_rouge = question_scores[0]['rouge-l']['f']  # F1分数
                
                # 计算与上下文的ROUGE分数
                context_scores = rouge.get_scores(prediction, context)
                context_rouge = context_scores[0]['rouge-l']['f']  # F1分数
                
                # 加权组合
                relevance = 0.3 * question_rouge + 0.7 * context_rouge
                return max(0.0, min(1.0, relevance))
            except Exception as e:
                logger.warning(f"ROUGE相关性计算失败: {e}")
                return rel_word_overlap(prediction, question, context)
        
        # 根据相关性类型选择计算方法
        if rel_type == 'semantic':
            return rel_semantic(prediction, question, context)
        elif rel_type == 'tfidf':
            return rel_tfidf(prediction, question, context)
        elif rel_type == 'weighted':
            return rel_weighted(prediction, question, context, weights)
        elif rel_type == 'rouge':
            return rel_rouge(prediction, question, context)
        else:
            # 默认使用词汇重叠
            return rel_word_overlap(prediction, question, context)

    @staticmethod
    def calculate_context_utilization(prediction: str, context: str, cal_type: str = 'simple', n: int = 2,
                                      weights: List[float] = None) -> float:
        """
        计算上下文利用率（答案使用了多少上下文信息）

        该方法通过多种方式评估预测答案对上下文信息的利用程度，包括词汇重叠、语义相似度、
        ROUGE分数、TF-IDF投影和N-gram匹配等。

        Args:
            prediction (str): 预测答案文本
            context (str): 上下文文本
            cal_type (str): 计算方式，可选值包括：
                - 'simple': 基于词汇重叠的简单计算（默认）
                - 'semantic': 基于SentenceTransformer的语义相似度
                - 'tfidf': 基于TF-IDF向量投影的计算
                - 'rouge': 基于ROUGE-L召回率的计算
                - 'ngram': 基于N-gram重叠的计算
                - 'weighted': 加权组合多种计算方式
            n (int): N-gram的N值，默认为2
            weights (List[float]): 各计算方式的权重列表，仅在cal_type='weighted'时使用，
                                 默认为[0.3, 0.3, 0.2, 0.2]，分别对应semantic、tfidf、rouge、ngram

        Returns:
            float: 上下文利用率，范围在0-1之间，值越高表示对上下文的利用越充分

        Note:
            - 当使用'semantic'或'weighted'模式时，需要预先加载SentenceTransformer模型
            - 所有计算结果都会被限制在[0,1]范围内
            - 如果计算过程中出现异常，会记录警告日志并返回默认值
        """
        if weights is None:
            weights = [0.3, 0.3, 0.2, 0.2]

        def cal_simple(prediction: str, context: str) -> float:
            """
            基于词汇重叠的简单上下文利用率计算
            
            计算预测答案中的词汇有多少来自上下文，反映答案对上下文的直接引用程度。
            """
            logger.debug(f"计算简单上下文利用率: prediction_length={len(prediction)}, context_length={len(context)}")

            pred_words = set(MetricsCalculator.normalize_text(prediction).split())
            context_words = set(MetricsCalculator.normalize_text(context).split())

            if not pred_words or not context_words:
                logger.debug("预测答案或上下文为空，返回利用率0.0")
                return 0.0

            # 预测答案中有多少来自上下文
            from_context = pred_words & context_words
            utilization = len(from_context) / len(pred_words)

            logger.debug(
                f"词汇重叠: 共同词汇数={len(from_context)}, 预测词汇数={len(pred_words)}, 利用率={utilization:.4f}")
            return utilization

        def cal_semantic(prediction: str, context: str) -> float:
            """
            基于语义相似度的上下文利用率计算
            
            使用SentenceTransformer计算预测答案与上下文的语义相似度，
            反映答案在语义层面与上下文的相关程度。
            """
            logger.debug("计算语义相似度上下文利用率")

            model = get_sentence_transformer_model()
            if model is not None:
                try:
                    logger.debug("编码预测答案和上下文...")
                    pred_embedding = model.encode(prediction)
                    context_embedding = model.encode(context)

                    # 计算余弦相似度
                    similarity = np.dot(pred_embedding, context_embedding) / (
                            np.linalg.norm(pred_embedding) * np.linalg.norm(context_embedding)
                    )

                    result = max(0.0, min(1.0, similarity))
                    logger.debug(f"语义相似度计算完成: {result:.4f}")
                    return result

                except Exception as e:
                    logger.warning(f"语义相似度计算失败: {e}")
                    return 0.0
            else:
                logger.warning("SentenceTransformer模型未加载，无法计算语义相似度")
                return 0.0

        def cal_rouge(prediction: str, context: str) -> float:
            """
            基于ROUGE-L召回率的上下文利用率计算
            
            使用ROUGE-L算法计算预测答案对上下文的召回率，
            反映答案在序列层面与上下文的匹配程度。
            """
            logger.debug("计算ROUGE-L上下文利用率")

            try:
                scores = rouge.get_scores(prediction, context)
                rouge_l_recall = scores[0]['rouge-l']['r']  # ROUGE-L召回率

                result = max(0.0, min(1.0, rouge_l_recall))
                logger.debug(f"ROUGE-L召回率计算完成: {result:.4f}")
                return result

            except Exception as e:
                logger.warning(f"ROUGE计算失败: {e}")
                return 0.0

        def cal_tfidf(prediction: str, context: str) -> float:
            """
            基于TF-IDF向量投影的上下文利用率计算
            
            将预测答案和上下文转换为TF-IDF向量，计算预测向量在上下文向量上的投影比例，
            反映答案在词汇重要性分布上与上下文的一致性。
            """
            logger.debug("计算TF-IDF上下文利用率")

            try:
                vectorizer = TfidfVectorizer()
                tfidf_matrix = vectorizer.fit_transform([prediction, context])

                pred_vector = tfidf_matrix[0]
                context_vector = tfidf_matrix[1]

                # 计算预测向量在上下文向量中的投影比例
                utilization = (pred_vector.dot(context_vector.T) /
                               context_vector.dot(context_vector.T))[0, 0]

                result = max(0.0, min(1.0, utilization))
                logger.debug(f"TF-IDF投影计算完成: {result:.4f}")
                return result

            except Exception as e:
                logger.warning(f"TF-IDF计算失败: {e}")
                return 0.0

        def cal_ngram(prediction: str, context: str, n: int = 2) -> float:
            """
            基于N-gram重叠的上下文利用率计算
            
            计算预测答案和上下文在N-gram级别的重叠程度，
            反映答案在短语层面与上下文的匹配情况。
            """
            logger.debug(f"计算{n}-gram上下文利用率")

            pred_ngrams = set(zip(*[MetricsCalculator.normalize_text(prediction).split()[i:] for i in range(n)]))
            context_ngrams = set(zip(*[MetricsCalculator.normalize_text(context).split()[i:] for i in range(n)]))

            if not pred_ngrams:
                logger.debug("预测答案N-gram为空，返回利用率0.0")
                return 0.0

            overlap = pred_ngrams & context_ngrams
            utilization = len(overlap) / len(pred_ngrams)

            logger.debug(
                f"N-gram重叠: 共同N-gram数={len(overlap)}, 预测N-gram数={len(pred_ngrams)}, 利用率={utilization:.4f}")
            return utilization

        def cal_weighted(prediction: str, context: str, n: int, weights: List[float]) -> float:
            """
            加权组合多种计算方式的上下文利用率
            
            综合语义相似度、TF-IDF投影、ROUGE-L召回率和N-gram重叠四种方式，
            通过加权平均得到综合的上下文利用率评估。
            """
            logger.debug(f"计算加权上下文利用率，权重: {weights}")

            if sum(weights) != 1:
                raise ValueError("权重之和必须为1")

            semantic_score = cal_semantic(prediction, context)
            tfidf_score = cal_tfidf(prediction, context)
            rouge_score = cal_rouge(prediction, context)
            ngram_score = cal_ngram(prediction, context, n)

            weighted_score = (semantic_score * weights[0] +
                              tfidf_score * weights[1] +
                              rouge_score * weights[2] +
                              ngram_score * weights[3])

            logger.debug(f"各分项得分: 语义={semantic_score:.4f}, TF-IDF={tfidf_score:.4f}, "
                         f"ROUGE={rouge_score:.4f}, N-gram={ngram_score:.4f}")
            logger.debug(f"加权综合得分: {weighted_score:.4f}")

            return weighted_score

        # 根据计算类型选择相应的方法
        logger.info(f"开始计算上下文利用率，计算方式: {cal_type}")

        if cal_type == 'semantic':
            result = cal_semantic(prediction, context)
        elif cal_type == 'tfidf':
            result = cal_tfidf(prediction, context)
        elif cal_type == 'rouge':
            result = cal_rouge(prediction, context)
        elif cal_type == 'ngram':
            result = cal_ngram(prediction, context, n)
        elif cal_type == 'weighted':
            result = cal_weighted(prediction, context, n, weights)
        else:  # 默认使用simple方式
            result = cal_simple(prediction, context)

        logger.info(f"上下文利用率计算完成: {result:.4f}")
        return result

    @staticmethod
    def calculate_completeness(prediction: str, ground_truth: List[str], cal_type: str = 'simple',
                               model_name: str = "zh_core_web_sm", weights: List[float] = None) -> float:
        """
        计算答案完整性
        
        Args:
            prediction (str): 预测答案
            ground_truth (List[str]): 标准答案列表
            cal_type (str): 计算方式，可选值包括：
                - 'simple': 基于长度比例的简单计算（默认）
                - 'coverage': 基于关键词覆盖度计算
                - 'entities': 基于命名实体识别计算
                - 'rouge': 基于ROUGE-1召回率计算
                - 'weighted': 加权组合多种计算方式
            model_name (str): 实体识别模型名称，默认为"zh_core_web_sm"
            weights (List[float]): 各计算方式的权重列表，仅在cal_type='weighted'时使用，
                                 默认为[0.5, 0.25, 0.25]，分别对应coverage、entities、rouge
            
        Returns:
            float: 完整性分数 (0-1)，值越高表示答案越完整
            
        Note:
            - 当使用'entities'或'weighted'模式时，需要安装spacy及相关语言模型
            - 所有计算结果都会被限制在[0,1]范围内
            - 如果计算过程中出现异常，会记录警告日志并返回默认值
        """
        if weights is None:
            weights = [0.5, 0.25, 0.25]

        def cal_simple(prediction: str, ground_truth: List[str]) -> float:
            """
            基于长度比例的简单完整性计算
            
            通过比较预测答案与标准答案的长度比例来评估完整性，
            避免答案过短或过长的情况。
            """
            logger.debug(f"计算简单完整性: prediction_length={len(prediction)}")

            pred_len = len(MetricsCalculator.normalize_text(prediction).split())
            if pred_len == 0:
                logger.debug("预测答案为空，返回完整性0.0")
                return 0.0

            # 计算与标准答案长度的接近程度
            best_score = 0.0
            for truth in ground_truth:
                truth_len = len(MetricsCalculator.normalize_text(truth).split())
                if truth_len == 0:
                    continue

                # 长度比例（预测答案不应太短也不应太长）
                ratio = min(pred_len / truth_len, truth_len / pred_len) if pred_len > 0 and truth_len > 0 else 0
                best_score = max(best_score, ratio)

            logger.debug(f"简单完整性计算完成: {best_score:.4f}")
            return best_score

        def cal_coverage(prediction: str, ground_truth: List[str]) -> float:
            """
            基于关键信息覆盖度计算答案完整性
            
            通过计算预测答案中包含的标准答案关键词比例来评估完整性。
            """
            logger.debug(
                f"计算覆盖度完整性: prediction_words={len(set(MetricsCalculator.normalize_text(prediction).split()))}")

            pred_words = set(MetricsCalculator.normalize_text(prediction).split())
            if not pred_words:
                logger.debug("预测答案词汇为空，返回完整性0.0")
                return 0.0

            best_coverage = 0.0
            for truth in ground_truth:
                truth_words = set(MetricsCalculator.normalize_text(truth).split())
                if not truth_words:
                    continue

                # 计算关键信息覆盖率
                covered = pred_words & truth_words
                coverage = len(covered) / len(truth_words) if truth_words else 0
                best_coverage = max(best_coverage, coverage)

            logger.debug(f"覆盖度完整性计算完成: {best_coverage:.4f}")
            return best_coverage

        def cal_entities(prediction: str, ground_truth: List[str], model_name: str = "zh_core_web_sm") -> float:
            """
            基于命名实体识别计算答案完整性
            
            使用spaCy进行命名实体识别，计算预测答案中包含的标准答案实体比例。
            """
            logger.debug(f"计算实体完整性: model={model_name}")

            try:
                import spacy
                nlp = spacy.load(model_name)

                pred_doc = nlp(prediction)
                pred_entities = set([ent.text for ent in pred_doc.ents])
                logger.debug(f"预测答案实体数: {len(pred_entities)}")

                if not pred_entities:
                    logger.debug("预测答案无实体，返回完整性0.0")
                    return 0.0

                best_entity_coverage = 0.0
                for truth in ground_truth:
                    truth_doc = nlp(truth)
                    truth_entities = set([ent.text for ent in truth_doc.ents])
                    logger.debug(f"标准答案实体数: {len(truth_entities)}")

                    if not truth_entities:
                        continue

                    covered_entities = pred_entities & truth_entities
                    entity_coverage = len(covered_entities) / len(truth_entities) if truth_entities else 0
                    best_entity_coverage = max(best_entity_coverage, entity_coverage)

                logger.debug(f"实体完整性计算完成: {best_entity_coverage:.4f}")
                return best_entity_coverage

            except ImportError:
                logger.warning(f"spaCy未安装，无法进行实体识别计算")
                return 0.0
            except Exception as e:
                logger.warning(f"实体识别计算失败: {e}")
                return 0.0

        def cal_rouge(prediction: str, ground_truth: List[str]) -> float:
            """
            基于ROUGE-1召回率计算答案完整性
            
            使用ROUGE-1算法计算预测答案对标准答案的召回率，
            反映答案在词汇层面的完整性。
            """
            logger.debug("计算ROUGE完整性")

            try:
                best_rouge_score = 0.0
                for truth in ground_truth:
                    scores = rouge.get_scores(prediction, truth)
                    # 使用ROUGE-1召回率作为完整性指标
                    rouge_score = scores[0]['rouge-1']['r']
                    best_rouge_score = max(best_rouge_score, rouge_score)

                logger.debug(f"ROUGE完整性计算完成: {best_rouge_score:.4f}")
                return best_rouge_score

            except Exception as e:
                logger.warning(f"ROUGE计算失败: {e}")
                return 0.0

        def cal_weighted(prediction: str, ground_truth: List[str], model_name: str = "zh_core_web_sm",
                         weights: List[float] = None) -> float:
            """
            加权组合多种计算方式的完整性评估
            
            综合关键词覆盖度、实体识别和ROUGE三种方式，
            通过加权平均得到综合的完整性评估。
            """
            if weights is None:
                weights = [0.5, 0.25, 0.25]

            logger.debug(f"计算加权完整性，权重: {weights}")

            if sum(weights) != 1:
                raise ValueError("权重和必须等于1")

            coverage_score = cal_coverage(prediction, ground_truth)
            entities_score = cal_entities(prediction, ground_truth, model_name)
            rouge_score = cal_rouge(prediction, ground_truth)

            weighted_score = (coverage_score * weights[0] +
                              entities_score * weights[1] +
                              rouge_score * weights[2])

            logger.debug(f"各分项得分: 覆盖度={coverage_score:.4f}, 实体={entities_score:.4f}, ROUGE={rouge_score:.4f}")
            logger.debug(f"加权综合得分: {weighted_score:.4f}")

            return weighted_score

        # 根据计算类型选择相应的方法
        logger.info(f"开始计算答案完整性，计算方式: {cal_type}")

        try:
            if cal_type == 'coverage':
                result = cal_coverage(prediction, ground_truth)
            elif cal_type == 'entities':
                result = cal_entities(prediction, ground_truth, model_name)
            elif cal_type == 'rouge':
                result = cal_rouge(prediction, ground_truth)
            elif cal_type == 'weighted':
                result = cal_weighted(prediction, ground_truth, model_name, weights)
            else:  # 默认使用simple方式
                result = cal_simple(prediction, ground_truth)

            # 确保结果在合理范围内
            result = max(0.0, min(1.0, result))
            logger.info(f"答案完整性计算完成: {result:.4f}")
            return result

        except Exception as e:
            logger.error(f"完整性计算过程中发生错误: {e}")
            return 0.0

    @staticmethod
    def calculate_conciseness(prediction: str, ground_truth: List[str], conciseness_type=None, weights: List[float] = None) -> float:
        """
        计算答案简洁性
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            conciseness_type: 简洁性计算类型 None(默认长度比例), ratio(长度比例), 
                             semantic(语义压缩度), rouge(ROUGE压缩度), weighted(加权组合)
            weights: 权重列表，仅在 conciseness_type='weighted' 时使用，默认[0.4, 0.4, 0.2]
            
        Returns:
            简洁性分数 (0-1)
        """

        def conciseness_length_ratio(prediction: str, ground_truth: List[str]) -> float:
            """基于长度比例的简洁性计算"""
            pred_len = len(MetricsCalculator.normalize_text(prediction).split())

            if pred_len == 0:
                return 0.0

            # 简洁性：与最短标准答案相比，不应过长
            min_truth_len = min(
                [len(MetricsCalculator.normalize_text(t).split()) for t in ground_truth],
                default=pred_len
            )

            if min_truth_len == 0:
                return 1.0 if pred_len <= 10 else 0.5

            # 如果预测答案比标准答案长很多，简洁性降低
            ratio = min_truth_len / pred_len if pred_len > 0 else 0
            return min(1.0, ratio * 1.5)  # 允许稍微长一点
        
        def conciseness_semantic_compression(prediction: str, ground_truth: List[str]) -> float:
            """基于语义压缩度的简洁性计算"""
            model = get_sentence_transformer_model()
            if model is not None:
                try:
                    pred_embedding = model.encode(prediction)
                    best_similarity = 0.0
                    
                    for truth in ground_truth:
                        truth_embedding = model.encode(truth)
                        # 计算语义相似度
                        similarity = np.dot(pred_embedding, truth_embedding) / (
                            np.linalg.norm(pred_embedding) * np.linalg.norm(truth_embedding)
                        )
                        best_similarity = max(best_similarity, similarity)
                    
                    # 结合长度因素：语义相似度高但长度短更好
                    pred_len = len(MetricsCalculator.normalize_text(prediction).split())
                    min_truth_len = min([len(MetricsCalculator.normalize_text(t).split()) for t in ground_truth])
                    length_factor = min(1.0, min_truth_len / pred_len) if pred_len > 0 else 0
                    
                    # 综合得分：语义相似度 × 长度因子
                    return max(0.0, min(1.0, best_similarity * length_factor))
                except Exception as e:
                    logger.warning(f"语义压缩度简洁性计算失败: {e}")
            
            # 回退到长度比例
            return conciseness_length_ratio(prediction, ground_truth)
        
        def conciseness_rouge_compression(prediction: str, ground_truth: List[str]) -> float:
            """基于ROUGE压缩度的简洁性计算"""
            try:
                best_rouge = 0.0
                pred_len = len(MetricsCalculator.normalize_text(prediction).split())
                
                for truth in ground_truth:
                    truth_len = len(MetricsCalculator.normalize_text(truth).split())
                    scores = rouge.get_scores(prediction, truth)
                    rouge_score = scores[0]['rouge-l']['f']  # F1分数
                    best_rouge = max(best_rouge, rouge_score)
                
                # 结合压缩率：ROUGE高且压缩率高更好
                compression_ratio = min(1.0, truth_len / pred_len) if pred_len > 0 else 0
                return max(0.0, min(1.0, best_rouge * compression_ratio))
            except Exception as e:
                logger.warning(f"ROUGE压缩度简洁性计算失败: {e}")
                return conciseness_length_ratio(prediction, ground_truth)
        

        
        def conciseness_information_density(prediction: str, ground_truth: List[str]) -> float:
            """基于信息密度的简洁性计算"""
            pred_words = set(MetricsCalculator.normalize_text(prediction).split())
            pred_len = len(pred_words)
            
            if pred_len == 0:
                return 0.0
            
            best_coverage = 0.0
            for truth in ground_truth:
                truth_words = set(MetricsCalculator.normalize_text(truth).split())
                if not truth_words:
                    continue
                covered = truth_words & pred_words
                coverage = len(covered) / len(truth_words)
                best_coverage = max(best_coverage, coverage)
            
            # 信息密度 = 信息覆盖率 / 长度
            density = best_coverage / pred_len if pred_len > 0 else 0
            # 归一化到0-1范围
            return min(1.0, density * len(pred_words))

        def conciseness_weighted(prediction: str, ground_truth: List[str], weights: List[float] = None) -> float:
            """加权组合多种简洁性计算方法"""
            if weights is None:
                weights = [0.4, 0.4, 0.2]  # 长度比例、语义压缩、ROUGE压缩的权重

            if len(weights) != 3 or abs(sum(weights) - 1.0) > 1e-6:
                raise ValueError("权重必须是长度为3的列表，且和为1")

            ratio_score = conciseness_length_ratio(prediction, ground_truth)
            semantic_score = conciseness_semantic_compression(prediction, ground_truth)
            rouge_score = conciseness_rouge_compression(prediction, ground_truth)

            weighted_score = (ratio_score * weights[0] +
                              semantic_score * weights[1] +
                              rouge_score * weights[2])
            return weighted_score
        # 根据简洁性类型选择计算方法
        if conciseness_type == 'semantic':
            return conciseness_semantic_compression(prediction, ground_truth)
        elif conciseness_type == 'rouge':
            return conciseness_rouge_compression(prediction, ground_truth)
        elif conciseness_type == 'weighted':
            return conciseness_weighted(prediction, ground_truth, weights)
        elif conciseness_type == 'density':
            return conciseness_information_density(prediction, ground_truth)
        else:
            # 默认使用长度比例
            return conciseness_length_ratio(prediction, ground_truth)


# ==================== 主评估器 ====================

class LLMEvaluator:
    """
    LLM 知识库问答评估器
    
    完整评估流程：
    1. 加载问答对数据集
    2. 加载LLM配置并测试连通性
    3. 进行问答，收集回答，保存临时文件
    4. 对比答案，计算各项指标
    5. 生成详细报告
    6. 保存结果，支持跨模型比较
    """

    def __init__(self, output_dir: str = "./evaluation_results", match_types: Dict[str, Any] = None):
        """
        初始化评估器
        
        Args:
            output_dir: 结果输出目录
            match_types: 匹配类型配置字典，用于自定义各指标的计算方式
                格式: {
                    "calculate_exact_match": {"match_type": "normalized"},
                    "calculate_f1_score": {"cal_type": "word"},
                    ...
                }
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.agents: Dict[str, BaseLLMAgent] = {}
        self.qa_pairs: List[QuestionAnswerPair] = []
        self.results: Dict[str, ModelEvaluationResult] = {}
        self.match_types: Dict[str, Any] = match_types or {}

        self.calculator = MetricsCalculator()

        logger.info(f"评估器初始化完成，输出目录: {self.output_dir}")
        if self.match_types:
            logger.info(f"已加载自定义 match_types 配置: {list(self.match_types.keys())}")

    def load_qa_pairs(self, source: str, source_type: str = 'auto',
                      split: str = 'test') -> List[QuestionAnswerPair]:
        """
        加载问答对
        
        Args:
            source: 数据源路径
            source_type: 数据源类型 (auto/hf_dataset/json/jsonl)
            split: 数据集分割（仅hf_dataset有效）
            
        Returns:
            问答对列表
        """
        # 自动检测类型
        if source_type == 'auto':
            if Path(source).is_dir():
                source_type = 'hf_dataset'
            elif source.endswith('.jsonl'):
                source_type = 'jsonl'
            else:
                source_type = 'json'

        # 根据类型加载
        if source_type == 'hf_dataset':
            self.qa_pairs = DatasetLoader.load_from_hf_dataset(source, split)
        elif source_type == 'jsonl':
            self.qa_pairs = DatasetLoader.load_from_jsonl(source)
        elif source_type == 'json':
            self.qa_pairs = DatasetLoader.load_from_json(source)
        else:
            raise ValueError(f"不支持的数据源类型: {source_type}")

        return self.qa_pairs

    def load_agents_from_config(self, config_path: str = None,
                                agents_config: List[Dict] = None) -> Dict[str, Tuple[bool, str]]:
        """
        从配置加载Agents并测试连通性
        
        Args:
            config_path: 配置文件路径
            agents_config: 直接传入的Agent配置列表
            
        Returns:
            连通性测试结果 {agent_name: (success, message)}
        """
        if config_path:
            config_manager = ConfigManager(config_path)
            agents_config = config_manager.get_agents_config()

        if not agents_config:
            raise ValueError("必须提供config_path或agents_config")

        connection_results = {}

        logger.info(f"正在加载 {len(agents_config)} 个Agent配置...")

        for agent_cfg in agents_config:
            name = agent_cfg.get('name', 'Unknown')
            try:
                agent = create_agent(agent_cfg)

                # 测试连通性
                success, message = agent.test_connection()
                connection_results[name] = (success, message)

                if success:
                    self.agents[name] = agent
                    logger.info(f"✓ Agent '{name}' 加载成功 - {message}")
                else:
                    logger.warning(f"✗ Agent '{name}' 连接测试失败 - {message}")

            except Exception as e:
                connection_results[name] = (False, str(e))
                logger.error(f"✗ Agent '{name}' 初始化失败: {e}")

        if not self.agents:
            logger.error("没有成功加载任何Agent")

        return connection_results

    def add_agent(self, agent_config: Dict, test_connection: bool = True) -> Tuple[bool, str]:
        """
        添加单个Agent
        
        Args:
            agent_config: Agent配置
            test_connection: 是否测试连通性
            
        Returns:
            (是否成功, 消息)
        """
        name = agent_config.get('name', 'Unknown')

        try:
            agent = create_agent(agent_config)

            if test_connection:
                success, message = agent.test_connection()
                if not success:
                    return False, f"连接测试失败: {message}"

            self.agents[name] = agent
            return True, "添加成功"

        except Exception as e:
            return False, str(e)

    def evaluate_single(self, agent_name: str, qa_pair: QuestionAnswerPair,
                        retry_attempts: int = 1, retry_delay: float = 1.0) -> ModelResponse:
        """
        评估单个问答对
        
        Args:
            agent_name: Agent名称
            qa_pair: 问答对
            retry_attempts: 重试次数
            retry_delay: 重试间隔（秒）
            
        Returns:
            模型响应
        """
        agent = self.agents.get(agent_name)
        if not agent:
            return ModelResponse(
                question_id=qa_pair.id,
                question=qa_pair.question,
                context=qa_pair.context,
                predicted_answer="",
                ground_truth=qa_pair.answers,
                success=False,
                inference_time=0,
                error_message=f"Agent '{agent_name}' 未找到"
            )

        # 重试机制
        last_error = ""
        for attempt in range(retry_attempts):
            try:
                result = agent.ask(qa_pair.question, qa_pair.context)
                if result.get('success'):
                    return ModelResponse(
                        question_id=qa_pair.id,
                        question=qa_pair.question,
                        context=qa_pair.context,
                        predicted_answer=result['answer'],
                        ground_truth=qa_pair.answers,
                        success=True,
                        inference_time=result.get('inference_time', 0),
                        metadata={
                            'usage': result.get('usage', {}),
                            'attempt': attempt + 1
                        }
                    )
                else:
                    last_error = result.get('error', '未知错误')

            except Exception as e:
                last_error = str(e)

            if attempt < retry_attempts - 1:
                time.sleep(retry_delay)

        # 所有重试都失败
        return ModelResponse(
            question_id=qa_pair.id,
            question=qa_pair.question,
            context=qa_pair.context,
            predicted_answer="",
            ground_truth=qa_pair.answers,
            success=False,
            inference_time=0,
            error_message=f"经过{retry_attempts}次尝试后仍然失败: {last_error}",
            metadata={'attempts': retry_attempts}
        )

    def evaluate_agent(self, agent_name: str, sample_size: int = None,
                       parallel: bool = False, max_workers: int = 4,
                       retry_attempts: int = 1, show_progress: bool = True,
                       match_types: Dict[str, Any] = None) -> ModelEvaluationResult:
        """
        评估单个Agent
        
        Args:
            agent_name: Agent名称
            sample_size: 采样数量（None表示全部）
            parallel: 是否并行处理
            max_workers: 并行工作线程数
            retry_attempts: 重试次数
            show_progress: 是否显示进度条
            match_types: 匹配类型配置字典（优先级高于初始化时的配置）
            
        Returns:
            评估结果
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' 不存在")

        if not self.qa_pairs:
            raise ValueError("请先加载问答对数据")

        # 使用传入的 match_types 或实例的 match_types
        effective_match_types = match_types if match_types is not None else self.match_types

        agent = self.agents[agent_name]

        # 确定评估样本
        eval_pairs = self.qa_pairs[:sample_size] if sample_size else self.qa_pairs
        total = len(eval_pairs)

        logger.info(f"开始评估 Agent '{agent_name}'，共 {total} 个样本")

        responses = []

        if parallel and total > 1:
            # 并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {
                    executor.submit(
                        self.evaluate_single, agent_name, pair, retry_attempts
                    ): i
                    for i, pair in enumerate(eval_pairs)
                }

                if show_progress:
                    pbar = tqdm(total=total, desc=f"评估 {agent_name}")

                for future in as_completed(future_to_idx):
                    response = future.result()
                    responses.append(response)

                    if show_progress:
                        pbar.update(1)

                if show_progress:
                    pbar.close()
        else:
            # 顺序处理
            iterator = tqdm(eval_pairs, desc=f"评估 {agent_name}") if show_progress else eval_pairs
            for pair in iterator:
                response = self.evaluate_single(agent_name, pair, retry_attempts)
                responses.append(response)

        # 按原始顺序排序
        responses.sort(key=lambda r: eval_pairs.index(next(
            p for p in eval_pairs if p.id == r.question_id
        )) if any(p.id == r.question_id for p in eval_pairs) else 0)

        # 计算指标（传入 match_types）
        metrics = self._calculate_metrics(responses, effective_match_types)

        # 构建结果
        result = ModelEvaluationResult(
            model_name=agent_name,
            model_version=agent.version,
            model_config=agent.get_config_dict(),
            metrics=metrics,
            responses=responses,
            evaluation_config={
                'sample_size': total,
                'parallel': parallel,
                'retry_attempts': retry_attempts,
                'match_types': effective_match_types,
                'timestamp': datetime.now().isoformat()
            }
        )

        self.results[agent_name] = result

        logger.info(f"Agent '{agent_name}' 评估完成:")
        logger.info(f"  - 精确匹配: {metrics.exact_match:.4f}")
        logger.info(f"  - F1分数: {metrics.f1_score:.4f}")
        logger.info(f"  - 语义相似度: {metrics.semantic_similarity:.4f}")
        logger.info(f"  - 平均推理时间: {metrics.avg_inference_time:.4f}秒")

        return result

    def evaluate_all(self, sample_size: int = None, parallel: bool = False,
                     max_workers: int = 4, retry_attempts: int = 1,
                     show_progress: bool = True, match_types: Dict[str, Any] = None) -> Dict[str, ModelEvaluationResult]:
        """
        评估所有Agent
        
        Args:
            sample_size: 采样数量
            parallel: 是否并行处理
            max_workers: 并行工作线程数
            retry_attempts: 重试次数
            show_progress: 是否显示进度条
            match_types: 匹配类型配置字典（优先级高于初始化时的配置）
            
        Returns:
            所有Agent的评估结果
        """
        for agent_name in self.agents.keys():
            self.evaluate_agent(
                agent_name=agent_name,
                sample_size=sample_size,
                parallel=parallel,
                max_workers=max_workers,
                retry_attempts=retry_attempts,
                show_progress=show_progress,
                match_types=match_types
            )

        return self.results

    def _get_metric_config(self, method_name: str, match_types: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取指定计算方法的配置参数
        
        Args:
            method_name: 计算方法名称（如 calculate_exact_match）
            match_types: match_types 配置字典
            
        Returns:
            该方法对应的配置参数字典
        """
        if not match_types or method_name not in match_types:
            return {}
        
        config = match_types.get(method_name, {})
        # 过滤掉 description 等非参数字段
        return {k: v for k, v in config.items() if k != 'description'}

    def _calculate_metrics(self, responses: List[ModelResponse], match_types: Dict[str, Any] = None) -> EvaluationMetrics:
        """
        计算评估指标
        
        Args:
            responses: 模型响应列表
            match_types: 匹配类型配置字典，用于自定义各指标的计算方式
            
        Returns:
            评估指标
        """
        total = len(responses)
        successful = [r for r in responses if r.success]
        failed = [r for r in responses if not r.success]

        if not successful:
            return EvaluationMetrics(
                total_samples=total,
                successful_predictions=0,
                failed_predictions=total
            )

        # 获取各指标的配置
        exact_match_config = self._get_metric_config('calculate_exact_match', match_types)
        f1_score_config = self._get_metric_config('calculate_f1_score', match_types)
        partial_match_config = self._get_metric_config('calculate_partial_match', match_types)
        semantic_sim_config = self._get_metric_config('calculate_semantic_similarity', match_types)
        coverage_config = self._get_metric_config('calculate_answer_coverage', match_types)
        relevance_config = self._get_metric_config('calculate_answer_relevance', match_types)
        utilization_config = self._get_metric_config('calculate_context_utilization', match_types)
        completeness_config = self._get_metric_config('calculate_completeness', match_types)
        conciseness_config = self._get_metric_config('calculate_conciseness', match_types)

        # 基础指标
        exact_matches = []
        f1_scores = []
        partial_matches = []
        semantic_sims = []
        inference_times = []

        # 知识库相关指标
        coverages = []
        relevances = []
        utilizations = []
        completeness_scores = []
        conciseness_scores = []

        for resp in successful:
            pred = resp.predicted_answer
            truth = resp.ground_truth

            # 基础指标（传入配置参数）
            exact_matches.append(self.calculator.calculate_exact_match(
                pred, truth, **exact_match_config
            ))
            f1_scores.append(self.calculator.calculate_f1_score(
                pred, truth, **f1_score_config
            ))
            partial_matches.append(self.calculator.calculate_partial_match(
                pred, truth, **partial_match_config
            ))
            semantic_sims.append(self.calculator.calculate_semantic_similarity(
                pred, truth, **semantic_sim_config
            ))
            inference_times.append(resp.inference_time)

            # 知识库指标（传入配置参数）
            coverages.append(self.calculator.calculate_answer_coverage(
                pred, truth, **coverage_config
            ))
            relevances.append(self.calculator.calculate_answer_relevance(
                pred, resp.question, resp.context, **relevance_config
            ))
            utilizations.append(self.calculator.calculate_context_utilization(
                pred, resp.context, **utilization_config
            ))
            completeness_scores.append(self.calculator.calculate_completeness(
                pred, truth, **completeness_config
            ))
            conciseness_scores.append(self.calculator.calculate_conciseness(
                pred, truth, **conciseness_config
            ))

        return EvaluationMetrics(
            total_samples=total,
            successful_predictions=len(successful),
            failed_predictions=len(failed),
            exact_match=np.mean(exact_matches),
            f1_score=np.mean(f1_scores),
            partial_match=np.mean(partial_matches),
            semantic_similarity=np.mean(semantic_sims),
            avg_inference_time=np.mean(inference_times),
            total_inference_time=np.sum(inference_times),
            answer_coverage=np.mean(coverages),
            answer_relevance=np.mean(relevances),
            context_utilization=np.mean(utilizations),
            answer_completeness=np.mean(completeness_scores),
            answer_conciseness=np.mean(conciseness_scores)
        )

    def save_intermediate_results(self, agent_name: str, responses: List[ModelResponse]):
        """
        保存中间结果（临时文件）
        
        Args:
            agent_name: Agent名称
            responses: 响应列表
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"intermediate_{agent_name}_{timestamp}.json"
        filepath = self.output_dir / 'intermediate' / filename

        ensure_directory_exists(str(filepath))

        data = {
            'agent_name': agent_name,
            'timestamp': timestamp,
            'total_responses': len(responses),
            'responses': [r.to_dict() for r in responses]
        }

        write_json_file(str(filepath), data)
        logger.info(f"中间结果已保存: {filepath}")

    def save_results(self, filename: str = None, detailed: bool = True):
        """
        保存评估结果
        
        Args:
            filename: 文件名（默认自动生成）
            detailed: 是否保存详细信息
        """
        if not self.results:
            logger.warning("没有评估结果可保存")
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"evaluation_results_{timestamp}.json"

        filepath = self.output_dir / filename

        data = {
            'evaluation_summary': {
                'total_agents': len(self.results),
                'total_qa_pairs': len(self.qa_pairs),
                'timestamp': datetime.now().isoformat(),
                'output_dir': str(self.output_dir)
            },
            'results': {}
        }

        for agent_name, result in self.results.items():
            if detailed:
                data['results'][agent_name] = result.to_dict()
            else:
                data['results'][agent_name] = {
                    'model_name': result.model_name,
                    'model_version': result.model_version,
                    'metrics': result.metrics.to_dict()
                }

        write_json_file(str(filepath), data)
        logger.info(f"评估结果已保存: {filepath}")

    def compare_models(self) -> Dict:
        """
        比较所有模型的表现
        
        Returns:
            比较结果
        """
        if len(self.results) < 2:
            logger.warning("至少需要2个模型的结果才能进行比较")
            return {}

        comparison = {
            'timestamp': datetime.now().isoformat(),
            'models_compared': list(self.results.keys()),
            'metrics_comparison': {},
            'rankings': {},
            'best_performers': {}
        }

        # 要比较的指标
        metrics_to_compare = [
            'exact_match', 'f1_score', 'semantic_similarity',
            'answer_coverage', 'answer_relevance', 'context_utilization',
            'answer_completeness', 'answer_conciseness', 'avg_inference_time'
        ]

        # 收集每个模型的指标
        for metric in metrics_to_compare:
            model_scores = []
            for agent_name, result in self.results.items():
                score = getattr(result.metrics, metric, 0)
                model_scores.append({
                    'model': agent_name,
                    'version': result.model_version,
                    'score': score
                })

            # 排序（时间越小越好，其他越大越好）
            reverse_sort = metric != 'avg_inference_time'
            model_scores.sort(key=lambda x: x['score'], reverse=reverse_sort)

            comparison['metrics_comparison'][metric] = model_scores
            comparison['rankings'][metric] = [m['model'] for m in model_scores]

            # 最佳表现者
            if model_scores:
                comparison['best_performers'][metric] = model_scores[0]

        # 综合排名
        total_scores = {}
        for agent_name in self.results.keys():
            # 计算综合分数（加权平均）
            metrics = self.results[agent_name].metrics
            score = (
                    metrics.exact_match * 0.25 +
                    metrics.f1_score * 0.25 +
                    metrics.semantic_similarity * 0.15 +
                    metrics.answer_coverage * 0.15 +
                    metrics.answer_relevance * 0.10 +
                    metrics.context_utilization * 0.10
            )
            total_scores[agent_name] = score

        # 按综合分数排序
        overall_ranking = sorted(
            total_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        comparison['overall_ranking'] = [
            {'model': name, 'score': score}
            for name, score in overall_ranking
        ]

        return comparison

    def save_comparison(self, filename: str = None):
        """
        保存模型比较结果
        
        Args:
            filename: 文件名
        """
        comparison = self.compare_models()

        if not comparison:
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"model_comparison_{timestamp}.json"

        filepath = self.output_dir / filename
        write_json_file(str(filepath), comparison)
        logger.info(f"模型比较结果已保存: {filepath}")

        # 打印比较摘要
        print("\n" + "=" * 60)
        print("模型比较结果")
        print("=" * 60)

        print("\n综合排名:")
        for i, item in enumerate(comparison['overall_ranking'], 1):
            print(f"  {i}. {item['model']}: {item['score']:.4f}")

        print("\n各指标最佳表现:")
        for metric, best in comparison['best_performers'].items():
            print(f"  {metric}: {best['model']} ({best['score']:.4f})")

    def generate_report(self, agent_name: str = None) -> str:
        """
        生成评估报告
        
        Args:
            agent_name: 指定Agent名称（None表示所有）
            
        Returns:
            报告文本
        """
        lines = []
        lines.append("=" * 70)
        lines.append("LLM 知识库问答评估报告")
        lines.append("=" * 70)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        agents_to_report = [agent_name] if agent_name else list(self.results.keys())

        for name in agents_to_report:
            if name not in self.results:
                lines.append(f"警告: 未找到 '{name}' 的评估结果")
                continue

            result = self.results[name]
            m = result.metrics

            lines.append(f"\n{'=' * 70}")
            lines.append(f"模型: {name} (版本: {result.model_version})")
            lines.append(f"{'=' * 70}")

            lines.append(f"\n样本统计:")
            lines.append(f"  总样本数: {m.total_samples}")
            lines.append(f"  成功预测: {m.successful_predictions}")
            lines.append(f"  失败预测: {m.failed_predictions}")
            lines.append(f"  成功率: {m.successful_predictions / m.total_samples * 100:.2f}%")

            lines.append(f"\n准确性指标:")
            lines.append(f"  精确匹配 (EM): {m.exact_match:.4f}")
            lines.append(f"  F1分数: {m.f1_score:.4f}")
            lines.append(f"  部分匹配: {m.partial_match:.4f}")
            lines.append(f"  语义相似度: {m.semantic_similarity:.4f}")

            lines.append(f"\n知识库能力指标:")
            lines.append(f"  答案覆盖率: {m.answer_coverage:.4f}")
            lines.append(f"  答案相关性: {m.answer_relevance:.4f}")
            lines.append(f"  上下文利用率: {m.context_utilization:.4f}")
            lines.append(f"  答案完整性: {m.answer_completeness:.4f}")
            lines.append(f"  答案简洁性: {m.answer_conciseness:.4f}")

            lines.append(f"\n效率指标:")
            lines.append(f"  平均推理时间: {m.avg_inference_time:.4f}秒")
            lines.append(f"  总推理时间: {m.total_inference_time:.2f}秒")

            # 失败案例分析
            failed_responses = [r for r in result.responses if not r.success]
            if failed_responses:
                lines.append(f"\n失败案例分析 (共 {len(failed_responses)} 个):")
                for i, resp in enumerate(failed_responses[:5], 1):
                    lines.append(f"  {i}. ID={resp.question_id}: {resp.error_message[:80]}...")

        lines.append("\n" + "=" * 70)
        lines.append("报告结束")
        lines.append("=" * 70)

        report = "\n".join(lines)
        return report

    def save_report(self, agent_name: str = None, filename: str = None):
        """
        保存评估报告到文件
        
        Args:
            agent_name: 指定Agent名称
            filename: 文件名
        """
        report = self.generate_report(agent_name)

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            agent_suffix = f"_{agent_name}" if agent_name else ""
            filename = f"evaluation_report{agent_suffix}_{timestamp}.txt"

        filepath = self.output_dir / filename
        ensure_directory_exists(str(filepath))

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"评估报告已保存: {filepath}")
        print(report)


# ==================== 便捷函数 ====================

def run_evaluation(
        qa_source: str,
        config_path: str = None,
        agents_config: List[Dict] = None,
        output_dir: str = "./evaluation_results",
        sample_size: int = None,
        parallel: bool = False,
        max_workers: int = 4,
        retry_attempts: int = 1,
        match_types: Dict[str, Any] = None
) -> Dict[str, ModelEvaluationResult]:
    """
    运行完整评估流程的便捷函数
    
    Args:
        qa_source: 问答对数据源路径
        config_path: Agent配置文件路径
        agents_config: 直接传入的Agent配置列表
        output_dir: 输出目录
        sample_size: 采样数量
        parallel: 是否并行处理
        max_workers: 并行工作线程数
        retry_attempts: 重试次数
        match_types: 匹配类型配置字典，用于自定义各指标的计算方式
            格式: {
                "calculate_exact_match": {"match_type": "normalized"},
                "calculate_f1_score": {"cal_type": "word"},
                ...
            }
        
    Returns:
        评估结果字典
    """
    # 如果未传入 match_types 但提供了 config_path，尝试从配置文件读取
    if match_types is None and config_path:
        try:
            config = read_json_file(config_path, default={})
            match_types = config.get('match_types')
            if match_types:
                logger.info("从配置文件加载 match_types 成功")
        except Exception as e:
            logger.warning(f"从配置文件加载 match_types 失败: {e}")

    # 创建评估器（传入 match_types）
    evaluator = LLMEvaluator(output_dir=output_dir, match_types=match_types)

    # 1. 加载问答对
    logger.info("步骤 1/6: 加载问答对...")
    evaluator.load_qa_pairs(qa_source)

    # 2. 加载Agents并测试连通性
    logger.info("步骤 2/6: 加载LLM配置并测试连通性...")
    evaluator.load_agents_from_config(config_path, agents_config)

    if not evaluator.agents:
        logger.error("没有可用的Agent，评估终止")
        return {}

    # 3. 进行评估（match_types 已通过初始化传入 evaluator）
    logger.info("步骤 3/6: 进行问答评估...")
    evaluator.evaluate_all(
        sample_size=sample_size,
        parallel=parallel,
        max_workers=max_workers,
        retry_attempts=retry_attempts
    )

    # 4. 保存临时结果（已在evaluate_all中完成）
    logger.info("步骤 4/6: 保存中间结果...")
    for agent_name, result in evaluator.results.items():
        evaluator.save_intermediate_results(agent_name, result.responses)

    # 5. 计算指标并生成报告
    logger.info("步骤 5/6: 计算评估指标...")
    evaluator.save_report()

    # 6. 保存最终结果和比较
    logger.info("步骤 6/6: 保存最终结果...")
    evaluator.save_results(detailed=True)
    evaluator.save_comparison()

    logger.info("评估流程完成！")
    return evaluator.results


# 保持向后兼容的别名
APIAgentEvaluator = LLMEvaluator

if __name__ == "__main__":
    # 使用示例
    print("LLM 知识库问答评估系统")
    print("=" * 50)
    print("\n使用示例:")
    print("""
    # 方式1: 使用便捷函数
    from src.llm.api_agent_evaluation import run_evaluation
    
    results = run_evaluation(
        qa_source="tests/my_datasets/hf_mirrors-google_xtreme",
        config_path="configs/agent_config.json",
        output_dir="./evaluation_results",
        sample_size=100,
        parallel=True,
        max_workers=4
    )
    
    # 方式2: 使用评估器类（更灵活）
    from src.llm.api_agent_evaluation import LLMEvaluator
    
    evaluator = LLMEvaluator(output_dir="./evaluation_results")
    
    # 加载问答对
    evaluator.load_qa_pairs("tests/my_datasets/hf_mirrors-google_xtreme")
    
    # 加载Agents
    evaluator.load_agents_from_config("configs/agent_config.json")
    
    # 评估
    evaluator.evaluate_all(sample_size=100)
    
    # 保存结果
    evaluator.save_results()
    evaluator.save_comparison()
    evaluator.save_report()
    """)
