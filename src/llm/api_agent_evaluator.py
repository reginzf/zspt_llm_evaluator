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
from typing import Dict, List, Tuple, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import re
import numpy as np
from tqdm import tqdm
from pathlib import Path
from difflib import SequenceMatcher
from rouge import Rouge

from env_config_init import settings, PROJECT_ROOT
from src.llm.data_loaders import DatasetLoader, QuestionAnswerPair, ModelResponse, ModelEvaluationResult, \
    EvaluationMetrics
from src.llm.llm_agent_basic import BaseLLMAgent, create_agent

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

from src.utils.pub_funs import write_json_file, read_json_file, ensure_directory_exists
from .config_manager import ConfigManager

# 模型根目录（兼容 Windows 和 Linux）
MODELS_DIR = PROJECT_ROOT / 'models'


# ==================== 模型管理器（单例模式，避免重复加载） ====================

class ModelManager:
    """
    模型管理器 - 统一管理各类ML模型的加载和复用
    使用单例模式确保模型只被加载一次
    """
    _instance = None
    _models: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def get_sentence_transformer(self):
        """获取或加载 SentenceTransformer 模型"""
        if 'sentence_transformer' not in self._models:
            try:
                from sentence_transformers import SentenceTransformer
                # 使用本地模型路径，优先使用 paraphrase-multilingual-MiniLM-L12-v2
                model_path = MODELS_DIR / 'paraphrase-multilingual-MiniLM-L12-v2'
                if not model_path.exists():
                    # 回退到 bge-base-zh-v1.5
                    model_path = MODELS_DIR / 'bge-base-zh-v1.5'
                if not model_path.exists():
                    logger.warning(f"本地 SentenceTransformer 模型不存在，尝试使用在线模型")
                    model_path = 'paraphrase-multilingual-MiniLM-L12-v2'
                
                logger.info(f"正在加载 SentenceTransformer 模型: {model_path}")
                self._models['sentence_transformer'] = SentenceTransformer(str(model_path))
                logger.info(f"SentenceTransformer模型加载完成")
            except Exception as e:
                logger.warning(f"SentenceTransformer模型加载失败: {e}")
                self._models['sentence_transformer'] = None
        return self._models['sentence_transformer']

    def get_bert_model(self):
        """获取或加载 BERT 模型"""
        if 'bert_model' not in self._models:
            try:
                from transformers import AutoTokenizer, AutoModel
                import torch
                
                bert_model_path = MODELS_DIR / 'bert-base-chinese'
                if not bert_model_path.exists():
                    logger.warning(f"本地 BERT 模型不存在: {bert_model_path}")
                    self._models['bert_model'] = None
                    self._models['bert_tokenizer'] = None
                else:
                    logger.info(f"正在加载 BERT 模型: {bert_model_path}")
                    tokenizer = AutoTokenizer.from_pretrained(str(bert_model_path))
                    model = AutoModel.from_pretrained(str(bert_model_path))
                    self._models['bert_tokenizer'] = tokenizer
                    self._models['bert_model'] = model
                    logger.info(f"BERT模型加载完成")
            except Exception as e:
                logger.warning(f"BERT模型加载失败: {e}")
                self._models['bert_model'] = None
                self._models['bert_tokenizer'] = None
        return self._models.get('bert_model'), self._models.get('bert_tokenizer')

    def get_word2vec_model(self):
        """获取或加载 Word2Vec 模型"""
        if 'word2vec' not in self._models:
            try:
                from gensim.models import KeyedVectors
                
                model_path = MODELS_DIR / 'text2vec-word2vec-tencent-chinese' / 'light_Tencent_AILab_ChineseEmbedding.bin'
                if not model_path.exists():
                    logger.warning(f"Word2Vec 模型文件不存在：{model_path}")
                    self._models['word2vec'] = None
                else:
                    logger.info(f"正在加载 Word2Vec 模型: {model_path}")
                    self._models['word2vec'] = KeyedVectors.load_word2vec_format(str(model_path), binary=True)
                    logger.info(f"Word2Vec模型加载完成")
            except Exception as e:
                logger.warning(f"Word2Vec模型加载失败: {e}")
                self._models['word2vec'] = None
        return self._models.get('word2vec')

    def get_spacy_model(self, model_name: str = "zh_core_web_sm"):
        """获取或加载 spaCy 模型"""
        cache_key = f'spacy_{model_name}'
        if cache_key not in self._models:
            try:
                import spacy
                logger.info(f"正在加载 spaCy 模型: {model_name}")
                self._models[cache_key] = spacy.load(model_name)
                logger.info(f"spaCy模型加载完成")
            except Exception as e:
                logger.warning(f"spaCy模型加载失败: {e}")
                self._models[cache_key] = None
        return self._models.get(cache_key)

    def clear_cache(self):
        """清除模型缓存，释放内存"""
        self._models.clear()
        logger.info("模型缓存已清除")


# 全局模型管理器实例
model_manager = ModelManager()


# ==================== 评估指标计算器 ====================

class MetricsCalculator:
    """
    评估指标计算器
    
    优化要点：
    1. 所有模型通过 ModelManager 统一管理，避免重复加载
    2. 指标计算结果统一为 0-1 之间的浮点数
    3. 每个指标提供多种计算方式，可根据场景选择
    """

    def __init__(self):
        self.rouge = Rouge()
        self.model_manager = model_manager
        logger.info("MetricsCalculator 初始化完成")

    @staticmethod
    def normalize_text(text: str) -> str:
        """标准化文本（用于比较）"""
        if not text:
            return ""
        # 转换为小写
        text = text.lower()
        # 移除标点符号
        text = re.sub(r'[^\w\s]', '', text)
        # 规范化空白
        text = ' '.join(text.split())
        return text.strip()

    def calculate_exact_match(self, prediction: str, ground_truth: List[str], match_type: str = None) -> float:
        """
        计算精确匹配率
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            match_type: 匹配类型 - normalized(标准化文本匹配), strict(严格匹配), 
                       fuzzy(模糊匹配，编辑距离>=0.9), semantic(语义相似度>=0.95)
            
        Returns:
            匹配率 (0.0-1.0) - 只要有一个标准答案匹配就返回1.0
        """
        if not prediction or not ground_truth:
            return 0.0

        pred_norm = self.normalize_text(prediction)
        if not pred_norm:
            return 0.0

        for truth in ground_truth:
            truth_norm = self.normalize_text(truth)
            if not truth_norm:
                continue

            if match_type == 'strict':
                # 严格匹配
                if prediction == truth:
                    return 1.0
            elif match_type == 'fuzzy':
                # 模糊匹配 - 编辑距离相似度
                similarity = SequenceMatcher(None, pred_norm, truth_norm).ratio()
                if similarity >= 0.9:
                    return 1.0
            elif match_type == 'semantic':
                # 语义匹配 - 使用SentenceTransformer
                model = self.model_manager.get_sentence_transformer()
                if model is not None:
                    try:
                        pred_emb = model.encode(prediction, show_progress_bar=False)
                        truth_emb = model.encode(truth, show_progress_bar=False)
                        similarity = np.dot(pred_emb, truth_emb) / (
                            np.linalg.norm(pred_emb) * np.linalg.norm(truth_emb)
                        )
                        if similarity >= 0.95:
                            return 1.0
                    except Exception as e:
                        logger.debug(f"语义匹配计算失败: {e}")
                        # 回退到标准化匹配
                        if pred_norm == truth_norm:
                            return 1.0
                else:
                    # 模型未加载，回退到标准化匹配
                    if pred_norm == truth_norm:
                        return 1.0
            else:
                # 默认：标准化匹配
                if pred_norm == truth_norm:
                    return 1.0
        
        return 0.0

    def calculate_f1_score(self, prediction: str, ground_truth: List[str], cal_type: str = 'word') -> float:
        """
        计算F1分数
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            cal_type: 计算方式 - word(词汇级), rouge(ROUGE-L), semantic(语义相似度), jaccard(Jaccard)
            
        Returns:
            F1分数 (0.0-1.0)
        """
        if not prediction or not ground_truth:
            return 0.0

        pred_norm = self.normalize_text(prediction)
        pred_tokens = pred_norm.split()
        
        if not pred_tokens:
            return 0.0

        best_f1 = 0.0

        for truth in ground_truth:
            truth_norm = self.normalize_text(truth)
            truth_tokens = truth_norm.split()
            
            if not truth_tokens:
                continue

            if cal_type == 'rouge':
                # 基于ROUGE-L F1分数
                try:
                    scores = self.rouge.get_scores(prediction, truth)
                    rouge_f1 = scores[0]['rouge-l']['f']
                    best_f1 = max(best_f1, rouge_f1)
                except Exception as e:
                    logger.debug(f"ROUGE F1计算失败: {e}")
                    # 回退到词汇级
                    f1 = self._calc_word_f1(pred_tokens, truth_tokens)
                    best_f1 = max(best_f1, f1)
            
            elif cal_type == 'semantic':
                # 基于语义相似度
                model = self.model_manager.get_sentence_transformer()
                if model is not None:
                    try:
                        pred_emb = model.encode(prediction, show_progress_bar=False)
                        truth_emb = model.encode(truth, show_progress_bar=False)
                        similarity = np.dot(pred_emb, truth_emb) / (
                            np.linalg.norm(pred_emb) * np.linalg.norm(truth_emb)
                        )
                        # 语义相似度直接作为F1的近似
                        best_f1 = max(best_f1, float(similarity))
                    except Exception as e:
                        logger.debug(f"语义F1计算失败: {e}")
                        f1 = self._calc_word_f1(pred_tokens, truth_tokens)
                        best_f1 = max(best_f1, f1)
                else:
                    f1 = self._calc_word_f1(pred_tokens, truth_tokens)
                    best_f1 = max(best_f1, f1)
            
            elif cal_type == 'jaccard':
                # 基于Jaccard相似度
                pred_set = set(pred_tokens)
                truth_set = set(truth_tokens)
                if len(pred_set) == 0 and len(truth_set) == 0:
                    return 1.0
                intersection = len(pred_set & truth_set)
                union = len(pred_set | truth_set)
                jaccard = intersection / union if union > 0 else 0
                best_f1 = max(best_f1, jaccard)
            
            else:
                # 默认：词汇级F1
                f1 = self._calc_word_f1(pred_tokens, truth_tokens)
                best_f1 = max(best_f1, f1)

        return best_f1

    def _calc_word_f1(self, pred_tokens: List[str], truth_tokens: List[str]) -> float:
        """计算词汇级F1分数"""
        if not pred_tokens or not truth_tokens:
            return 0.0
        
        common = set(pred_tokens) & set(truth_tokens)
        if not common:
            return 0.0
        
        precision = len(common) / len(pred_tokens)
        recall = len(common) / len(truth_tokens)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * precision * recall / (precision + recall)

    def calculate_semantic_similarity(self, prediction: str, ground_truth: List[str], sim_type: str = 'sentence') -> float:
        """
        计算语义相似度
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            sim_type: 相似度类型 - sentence(SentenceTransformer), bert(BERT), tfidf(TF-IDF), jaccard(Jaccard)
            
        Returns:
            语义相似度 (0.0-1.0)
        """
        if not prediction or not ground_truth:
            return 0.0

        best_similarity = 0.0

        for truth in ground_truth:
            if sim_type == 'bert':
                # BERT语义相似度
                model, tokenizer = self.model_manager.get_bert_model()
                if model is not None and tokenizer is not None:
                    try:
                        import torch
                        
                        def get_bert_embedding(text):
                            inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
                            with torch.no_grad():
                                outputs = model(**inputs)
                            return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                        
                        pred_emb = get_bert_embedding(prediction)
                        truth_emb = get_bert_embedding(truth)
                        similarity = np.dot(pred_emb, truth_emb) / (
                            np.linalg.norm(pred_emb) * np.linalg.norm(truth_emb)
                        )
                        best_similarity = max(best_similarity, float(similarity))
                    except Exception as e:
                        logger.debug(f"BERT相似度计算失败: {e}")
                        # 回退到SentenceTransformer
                        sim = self._calc_sentence_similarity(prediction, truth)
                        best_similarity = max(best_similarity, sim)
                else:
                    sim = self._calc_sentence_similarity(prediction, truth)
                    best_similarity = max(best_similarity, sim)
            
            elif sim_type == 'tfidf':
                # TF-IDF相似度
                try:
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    vectorizer = TfidfVectorizer()
                    tfidf_matrix = vectorizer.fit_transform([prediction, truth])
                    similarity = (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
                    best_similarity = max(best_similarity, float(similarity))
                except Exception as e:
                    logger.debug(f"TF-IDF相似度计算失败: {e}")
                    # 回退到Jaccard
                    sim = self._calc_jaccard_similarity(prediction, truth)
                    best_similarity = max(best_similarity, sim)
            
            elif sim_type == 'jaccard':
                # Jaccard相似度
                sim = self._calc_jaccard_similarity(prediction, truth)
                best_similarity = max(best_similarity, sim)
            
            else:
                # 默认：SentenceTransformer
                sim = self._calc_sentence_similarity(prediction, truth)
                best_similarity = max(best_similarity, sim)

        return min(1.0, max(0.0, best_similarity))

    def _calc_sentence_similarity(self, prediction: str, truth: str) -> float:
        """使用SentenceTransformer计算语义相似度"""
        model = self.model_manager.get_sentence_transformer()
        if model is None:
            # 模型未加载，回退到Jaccard
            return self._calc_jaccard_similarity(prediction, truth)
        
        try:
            pred_emb = model.encode(prediction, show_progress_bar=False)
            truth_emb = model.encode(truth, show_progress_bar=False)
            similarity = np.dot(pred_emb, truth_emb) / (
                np.linalg.norm(pred_emb) * np.linalg.norm(truth_emb)
            )
            return float(similarity)
        except Exception as e:
            logger.debug(f"SentenceTransformer相似度计算失败: {e}")
            return self._calc_jaccard_similarity(prediction, truth)

    def _calc_jaccard_similarity(self, prediction: str, truth: str) -> float:
        """计算Jaccard相似度"""
        pred_words = set(self.normalize_text(prediction).split())
        truth_words = set(self.normalize_text(truth).split())
        
        if len(pred_words) == 0 and len(truth_words) == 0:
            return 1.0
        if len(pred_words) == 0 or len(truth_words) == 0:
            return 0.0
        
        intersection = len(pred_words & truth_words)
        union = len(pred_words | truth_words)
        return intersection / union if union > 0 else 0.0

    def calculate_answer_relevance(self, prediction: str, question: str, context: str, 
                                    rel_type: str = 'word', weights: List[float] = None) -> float:
        """
        计算答案与问题的相关性
        
        Args:
            prediction: 预测答案
            question: 问题
            context: 上下文
            rel_type: 相关性计算类型 - word(词汇重叠), semantic(语义相似度), tfidf, rouge, weighted(加权组合)
            weights: 加权计算的权重列表 [word_overlap_weight, semantic_weight, tfidf_weight]
            
        Returns:
            相关性分数 (0.0-1.0)
        """
        if not prediction:
            return 0.0

        if rel_type == 'semantic':
            # 语义相关性
            model = self.model_manager.get_sentence_transformer()
            if model is not None:
                try:
                    pred_emb = model.encode(prediction, show_progress_bar=False)
                    question_emb = model.encode(question, show_progress_bar=False)
                    context_emb = model.encode(context, show_progress_bar=False)
                    
                    question_sim = np.dot(pred_emb, question_emb) / (
                        np.linalg.norm(pred_emb) * np.linalg.norm(question_emb)
                    )
                    context_sim = np.dot(pred_emb, context_emb) / (
                        np.linalg.norm(pred_emb) * np.linalg.norm(context_emb)
                    )
                    
                    # 加权组合：30%问题相关性 + 70%上下文相关性
                    relevance = 0.3 * question_sim + 0.7 * context_sim
                    return min(1.0, max(0.0, relevance))
                except Exception as e:
                    logger.debug(f"语义相关性计算失败: {e}")
                    # 回退到词汇级
                    return self._calc_word_relevance(prediction, question, context)
            else:
                return self._calc_word_relevance(prediction, question, context)
        
        elif rel_type == 'weighted' and weights:
            # 加权组合：word_overlap, semantic, tfidf
            scores = []
            
            # word_overlap 分数
            word_score = self._calc_word_relevance(prediction, question, context)
            scores.append(word_score)
            
            # semantic 分数
            semantic_score = word_score  # 默认回退
            model = self.model_manager.get_sentence_transformer()
            if model is not None:
                try:
                    pred_emb = model.encode(prediction, show_progress_bar=False)
                    question_emb = model.encode(question, show_progress_bar=False)
                    context_emb = model.encode(context, show_progress_bar=False)
                    
                    question_sim = np.dot(pred_emb, question_emb) / (
                        np.linalg.norm(pred_emb) * np.linalg.norm(question_emb)
                    )
                    context_sim = np.dot(pred_emb, context_emb) / (
                        np.linalg.norm(pred_emb) * np.linalg.norm(context_emb)
                    )
                    semantic_score = 0.3 * question_sim + 0.7 * context_sim
                except Exception as e:
                    logger.debug(f"语义相关性计算失败: {e}")
            scores.append(semantic_score)
            
            # tfidf 分数（使用词汇重叠作为近似）
            tfidf_score = word_score
            scores.append(tfidf_score)
            
            # 加权计算
            weighted_score = sum(w * s for w, s in zip(weights, scores))
            return min(1.0, max(0.0, weighted_score))
        
        else:
            # 默认：词汇级相关性
            return self._calc_word_relevance(prediction, question, context)

    def _calc_word_relevance(self, prediction: str, question: str, context: str) -> float:
        """计算词汇级相关性"""
        pred_words = set(self.normalize_text(prediction).split())
        question_words = set(self.normalize_text(question).split())
        context_words = set(self.normalize_text(context).split())
        
        if not pred_words:
            return 0.0
        
        # 计算与问题的重叠
        question_overlap = len(pred_words & question_words) / len(pred_words) if pred_words else 0
        
        # 计算与上下文的重叠
        context_overlap = len(pred_words & context_words) / len(pred_words) if pred_words else 0
        
        # 加权组合：30%问题 + 70%上下文
        return min(1.0, 0.3 * question_overlap + 0.7 * context_overlap)

    def calculate_context_utilization(self, prediction: str, context: str, 
                                       cal_type: str = 'simple', weights: List[float] = None, 
                                       n: int = 2) -> float:
        """
        计算上下文利用率（答案使用了多少上下文信息）
        
        Args:
            prediction: 预测答案
            context: 上下文文本
            cal_type: 计算方式 - simple(词汇重叠), semantic(语义相似度), rouge(ROUGE-L召回率), weighted(加权)
            weights: 加权计算的权重列表 [semantic_weight, tfidf_weight, rouge_weight, ngram_weight]
            n: N-gram的N值
            
        Returns:
            上下文利用率 (0.0-1.0)
        """
        if not prediction or not context:
            return 0.0

        # weighted 模式
        if cal_type == 'weighted' and weights:
            scores = []
            
            # semantic 分数
            semantic_score = 0.0
            model = self.model_manager.get_sentence_transformer()
            if model is not None:
                try:
                    pred_emb = model.encode(prediction, show_progress_bar=False)
                    context_emb = model.encode(context, show_progress_bar=False)
                    semantic_score = np.dot(pred_emb, context_emb) / (
                        np.linalg.norm(pred_emb) * np.linalg.norm(context_emb)
                    )
                except Exception as e:
                    logger.debug(f"语义利用率计算失败: {e}")
            scores.append(semantic_score)
            
            # tfidf 分数（使用简单词汇重叠近似）
            tfidf_score = self._calc_simple_utilization(prediction, context)
            scores.append(tfidf_score)
            
            # rouge 分数
            rouge_score = 0.0
            try:
                scores_rouge = self.rouge.get_scores(prediction, context)
                rouge_score = scores_rouge[0]['rouge-l']['r']
            except Exception as e:
                logger.debug(f"ROUGE利用率计算失败: {e}")
            scores.append(rouge_score)
            
            # ngram 分数
            ngram_score = self._calc_ngram_utilization(prediction, context, n)
            scores.append(ngram_score)
            
            # 加权计算
            weighted_score = sum(w * s for w, s in zip(weights, scores))
            return min(1.0, max(0.0, weighted_score))

        if cal_type == 'semantic':
            # 语义相似度
            model = self.model_manager.get_sentence_transformer()
            if model is not None:
                try:
                    pred_emb = model.encode(prediction, show_progress_bar=False)
                    context_emb = model.encode(context, show_progress_bar=False)
                    similarity = np.dot(pred_emb, context_emb) / (
                        np.linalg.norm(pred_emb) * np.linalg.norm(context_emb)
                    )
                    return min(1.0, max(0.0, float(similarity)))
                except Exception as e:
                    logger.debug(f"语义利用率计算失败: {e}")
                    return self._calc_simple_utilization(prediction, context)
            else:
                return self._calc_simple_utilization(prediction, context)
        
        elif cal_type == 'rouge':
            # ROUGE-L召回率
            try:
                scores = self.rouge.get_scores(prediction, context)
                rouge_recall = scores[0]['rouge-l']['r']
                return min(1.0, max(0.0, rouge_recall))
            except Exception as e:
                logger.debug(f"ROUGE利用率计算失败: {e}")
                return self._calc_simple_utilization(prediction, context)
        
        else:
            # 默认：简单词汇重叠
            return self._calc_simple_utilization(prediction, context)

    def _calc_simple_utilization(self, prediction: str, context: str) -> float:
        """计算简单词汇利用率"""
        pred_words = set(self.normalize_text(prediction).split())
        context_words = set(self.normalize_text(context).split())
        
        if not pred_words or not context_words:
            return 0.0
        
        # 预测答案中有多少来自上下文
        from_context = pred_words & context_words
        return len(from_context) / len(pred_words)

    def _calc_ngram_utilization(self, prediction: str, context: str, n: int = 2) -> float:
        """计算N-gram利用率"""
        pred_norm = self.normalize_text(prediction)
        context_norm = self.normalize_text(context)
        
        pred_tokens = pred_norm.split()
        context_tokens = context_norm.split()
        
        if len(pred_tokens) < n or len(context_tokens) < n:
            return self._calc_simple_utilization(prediction, context)
        
        # 构建N-gram集合
        pred_ngrams = set(tuple(pred_tokens[i:i+n]) for i in range(len(pred_tokens) - n + 1))
        context_ngrams = set(tuple(context_tokens[i:i+n]) for i in range(len(context_tokens) - n + 1))
        
        if not pred_ngrams:
            return 0.0
        
        # 计算重叠的N-gram比例
        overlap = pred_ngrams & context_ngrams
        return len(overlap) / len(pred_ngrams)

    def calculate_completeness(self, prediction: str, ground_truth: List[str], 
                                cal_type: str = 'coverage', weights: List[float] = None) -> float:
        """
        计算答案完整性
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            cal_type: 计算方式 - coverage(关键词覆盖度), rouge(ROUGE-1召回率), simple(长度比例), weighted(加权)
            weights: 加权计算的权重列表 [coverage_weight, entities_weight, rouge_weight]
            
        Returns:
            完整性分数 (0.0-1.0)
        """
        if not prediction or not ground_truth:
            return 0.0

        # weighted 模式
        if cal_type == 'weighted' and weights:
            best_score = 0.0
            for truth in ground_truth:
                scores = []
                
                # coverage 分数
                pred_words = set(self.normalize_text(prediction).split())
                truth_words = set(self.normalize_text(truth).split())
                coverage_score = len(pred_words & truth_words) / len(truth_words) if truth_words else 0
                scores.append(coverage_score)
                
                # entities 分数（使用词汇覆盖近似）
                entities_score = coverage_score
                scores.append(entities_score)
                
                # rouge 分数
                rouge_score = 0.0
                try:
                    scores_rouge = self.rouge.get_scores(prediction, truth)
                    rouge_score = scores_rouge[0]['rouge-1']['r']
                except Exception as e:
                    logger.debug(f"ROUGE完整性计算失败: {e}")
                scores.append(rouge_score)
                
                # 加权计算
                weighted_score = sum(w * s for w, s in zip(weights, scores))
                best_score = max(best_score, weighted_score)
            
            return min(1.0, max(0.0, best_score))

        pred_norm = self.normalize_text(prediction)
        pred_words = set(pred_norm.split())
        pred_len = len(pred_norm.split())

        if cal_type == 'rouge':
            # ROUGE-1召回率
            best_score = 0.0
            for truth in ground_truth:
                try:
                    scores = self.rouge.get_scores(prediction, truth)
                    rouge_score = scores[0]['rouge-1']['r']
                    best_score = max(best_score, rouge_score)
                except Exception as e:
                    logger.debug(f"ROUGE完整性计算失败: {e}")
                    continue
            return best_score
        
        elif cal_type == 'simple':
            # 基于长度比例
            if pred_len == 0:
                return 0.0
            
            best_score = 0.0
            for truth in ground_truth:
                truth_len = len(self.normalize_text(truth).split())
                if truth_len == 0:
                    continue
                # 长度比例（预测答案不应太短也不应太长）
                ratio = min(pred_len / truth_len, truth_len / pred_len) if pred_len > 0 and truth_len > 0 else 0
                best_score = max(best_score, ratio)
            return best_score
        
        else:
            # 默认：关键词覆盖度
            if not pred_words:
                return 0.0
            
            best_coverage = 0.0
            for truth in ground_truth:
                truth_words = set(self.normalize_text(truth).split())
                if not truth_words:
                    continue
                covered = pred_words & truth_words
                coverage = len(covered) / len(truth_words) if truth_words else 0
                best_coverage = max(best_coverage, coverage)
            return best_coverage

    def calculate_conciseness(self, prediction: str, ground_truth: List[str], 
                               cal_type: str = 'ratio', weights: List[float] = None) -> float:
        """
        计算答案简洁性
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            cal_type: 计算方式 - ratio(长度比例), rouge(ROUGE压缩率), weighted(加权)
            weights: 加权计算的权重列表 [ratio_weight, semantic_weight, rouge_weight]
            
        Returns:
            简洁性分数 (0.0-1.0) - 越高表示越简洁
        """
        if not prediction or not ground_truth:
            return 0.0

        pred_len = len(self.normalize_text(prediction).split())
        if pred_len == 0:
            return 0.0

        # weighted 模式
        if cal_type == 'weighted' and weights:
            best_score = 0.0
            for truth in ground_truth:
                scores = []
                
                # ratio 分数（长度比例）
                truth_len = len(self.normalize_text(truth).split())
                ratio_score = min(1.0, (truth_len / pred_len if pred_len > 0 else 0) * 1.5)
                scores.append(ratio_score)
                
                # semantic 分数（使用语义相似度近似）
                semantic_score = 0.0
                model = self.model_manager.get_sentence_transformer()
                if model is not None:
                    try:
                        pred_emb = model.encode(prediction, show_progress_bar=False)
                        truth_emb = model.encode(truth, show_progress_bar=False)
                        semantic_score = np.dot(pred_emb, truth_emb) / (
                            np.linalg.norm(pred_emb) * np.linalg.norm(truth_emb)
                        )
                    except Exception as e:
                        logger.debug(f"语义简洁性计算失败: {e}")
                scores.append(semantic_score)
                
                # rouge 分数
                rouge_score = 0.0
                try:
                    scores_rouge = self.rouge.get_scores(prediction, truth)
                    rouge_f = scores_rouge[0]['rouge-l']['f']
                    compression = min(1.0, truth_len / pred_len) if pred_len > 0 else 0
                    rouge_score = rouge_f * compression
                except Exception as e:
                    logger.debug(f"ROUGE简洁性计算失败: {e}")
                scores.append(rouge_score)
                
                # 加权计算
                weighted_score = sum(w * s for w, s in zip(weights, scores))
                best_score = max(best_score, weighted_score)
            
            return min(1.0, max(0.0, best_score))

        if cal_type == 'rouge':
            # 基于ROUGE的压缩率
            best_score = 0.0
            for truth in ground_truth:
                try:
                    truth_len = len(self.normalize_text(truth).split())
                    scores = self.rouge.get_scores(prediction, truth)
                    rouge_score = scores[0]['rouge-l']['f']
                    # 结合ROUGE分数和压缩率
                    compression = min(1.0, truth_len / pred_len) if pred_len > 0 else 0
                    score = rouge_score * compression
                    best_score = max(best_score, score)
                except Exception as e:
                    logger.debug(f"ROUGE简洁性计算失败: {e}")
                    continue
            return best_score
        
        else:
            # 默认：长度比例
            min_truth_len = min(
                [len(self.normalize_text(t).split()) for t in ground_truth],
                default=pred_len
            )
            
            if min_truth_len == 0:
                return 1.0 if pred_len <= 10 else 0.5
            
            # 如果预测答案比标准答案长很多，简洁性降低
            ratio = min_truth_len / pred_len if pred_len > 0 else 0
            return min(1.0, ratio * 1.5)  # 允许稍微长一点

    def calculate_answer_coverage(self, prediction: str, ground_truth: List[str], 
                                   cal_type: str = 'word', weights: List[float] = None) -> float:
        """
        计算答案覆盖率（预测答案包含标准答案信息的程度）
        
        Args:
            prediction: 预测答案
            ground_truth: 标准答案列表
            cal_type: 计算方式 - word(词汇覆盖), rouge(ROUGE-L召回率), semantic(语义相似度), weighted(加权)
            weights: 加权计算的权重列表 [rouge_weight, sentence_weight]
            
        Returns:
            覆盖率 (0.0-1.0)
        """
        if not prediction or not ground_truth:
            return 0.0

        # weighted 模式：加权计算 rouge 和 sentence
        if cal_type == 'weighted' and weights:
            best_coverage = 0.0
            for truth in ground_truth:
                rouge_score = 0.0
                sentence_score = 0.0
                
                # rouge 分数
                try:
                    scores = self.rouge.get_scores(prediction, truth)
                    rouge_score = scores[0]['rouge-l']['r']
                except Exception as e:
                    logger.debug(f"ROUGE覆盖率计算失败: {e}")
                
                # sentence 分数（基于词汇覆盖）
                sentence_score = self._calc_word_coverage(prediction, truth)
                
                # 加权计算
                weighted_score = weights[0] * rouge_score + weights[1] * sentence_score
                best_coverage = max(best_coverage, weighted_score)
            
            return min(1.0, max(0.0, best_coverage))

        best_coverage = 0.0

        for truth in ground_truth:
            if cal_type == 'rouge':
                try:
                    scores = self.rouge.get_scores(prediction, truth)
                    rouge_recall = scores[0]['rouge-l']['r']
                    best_coverage = max(best_coverage, rouge_recall)
                except Exception as e:
                    logger.debug(f"ROUGE覆盖率计算失败: {e}")
                    # 回退到词汇级
                    coverage = self._calc_word_coverage(prediction, truth)
                    best_coverage = max(best_coverage, coverage)
            
            elif cal_type == 'semantic':
                model = self.model_manager.get_sentence_transformer()
                if model is not None:
                    try:
                        pred_emb = model.encode(prediction, show_progress_bar=False)
                        truth_emb = model.encode(truth, show_progress_bar=False)
                        similarity = np.dot(pred_emb, truth_emb) / (
                            np.linalg.norm(pred_emb) * np.linalg.norm(truth_emb)
                        )
                        best_coverage = max(best_coverage, float(similarity))
                    except Exception as e:
                        logger.debug(f"语义覆盖率计算失败: {e}")
                        coverage = self._calc_word_coverage(prediction, truth)
                        best_coverage = max(best_coverage, coverage)
                else:
                    coverage = self._calc_word_coverage(prediction, truth)
                    best_coverage = max(best_coverage, coverage)
            
            else:
                # 默认：词汇覆盖
                coverage = self._calc_word_coverage(prediction, truth)
                best_coverage = max(best_coverage, coverage)

        return min(1.0, max(0.0, best_coverage))

    def _calc_word_coverage(self, prediction: str, truth: str) -> float:
        """计算词汇覆盖率"""
        pred_words = set(self.normalize_text(prediction).split())
        truth_words = set(self.normalize_text(truth).split())
        
        if not truth_words:
            return 0.0
        if not pred_words:
            return 0.0
        
        covered = truth_words & pred_words
        return len(covered) / len(truth_words)

    def compute_all_metrics_for_single(
        self,
        prediction: str,
        question: str,
        context: str,
        ground_truth: List[str],
        match_types: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """
        计算单个问题的所有指标
        
        Args:
            prediction: 预测答案
            question: 问题
            context: 上下文
            ground_truth: 标准答案列表
            match_types: 各指标的计算方式配置
            
        Returns:
            包含所有指标的字典
        """
        match_types = match_types or {}
        
        # 获取各指标的配置
        exact_match_config = match_types.get('calculate_exact_match', {})
        f1_config = match_types.get('calculate_f1_score', {})
        semantic_config = match_types.get('calculate_semantic_similarity', {})
        coverage_config = match_types.get('calculate_answer_coverage', {})
        relevance_config = match_types.get('calculate_answer_relevance', {})
        utilization_config = match_types.get('calculate_context_utilization', {})
        completeness_config = match_types.get('calculate_completeness', {})
        conciseness_config = match_types.get('calculate_conciseness', {})
        
        return {
            'exact_match': self.calculate_exact_match(prediction, ground_truth, **exact_match_config),
            'f1_score': self.calculate_f1_score(prediction, ground_truth, **f1_config),
            'semantic_similarity': self.calculate_semantic_similarity(prediction, ground_truth, **semantic_config),
            'answer_coverage': self.calculate_answer_coverage(prediction, ground_truth, **coverage_config),
            'answer_relevance': self.calculate_answer_relevance(prediction, question, context, **relevance_config),
            'context_utilization': self.calculate_context_utilization(prediction, context, **utilization_config),
            'answer_completeness': self.calculate_completeness(prediction, ground_truth, **completeness_config),
            'answer_conciseness': self.calculate_conciseness(prediction, ground_truth, **conciseness_config),
        }


# ==================== 主评估器 ====================

class LLMEvaluator:
    """
    LLM 知识库问答评估器
    
    完整评估流程：
    1. 加载问答对数据集
    2. 加载LLM配置并测试连通性
    3. 进行问答，收集回答，保存临时文件
    4. 对比答案，计算各项指标（包括每个问题的详细指标）
    5. 生成详细报告
    6. 保存结果，支持跨模型比较
    """

    def __init__(self, output_dir: str = "./evaluation_results", match_types: Dict[str, Any] = None):
        """
        初始化评估器
        
        Args:
            output_dir: 结果输出目录
            match_types: 匹配类型配置字典，用于自定义各指标的计算方式
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

        # 计算指标（传入 match_types，并计算每个问题的详细指标）
        metrics, question_metrics = self._calculate_metrics_with_details(responses, effective_match_types)

        # 将每个问题的指标添加到response中
        for resp in responses:
            if resp.question_id in question_metrics:
                resp.metrics = question_metrics[resp.question_id]

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
            },
            question_metrics=question_metrics
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
                     show_progress: bool = True, match_types: Dict[str, Any] = None) -> Dict[
        str, ModelEvaluationResult]:
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

    def _calculate_metrics(self, responses: List[ModelResponse],
                           match_types: Dict[str, Any] = None) -> EvaluationMetrics:
        """
        计算评估指标（仅汇总指标，保留向后兼容）
        
        Args:
            responses: 模型响应列表
            match_types: 匹配类型配置字典，用于自定义各指标的计算方式
            
        Returns:
            评估指标
        """
        metrics, _ = self._calculate_metrics_with_details(responses, match_types)
        return metrics

    def _calculate_metrics_with_details(
        self,
        responses: List[ModelResponse],
        match_types: Dict[str, Any] = None
    ) -> Tuple[EvaluationMetrics, Dict[str, Dict[str, float]]]:
        """
        计算评估指标，同时返回每个问题的详细指标
        
        Args:
            responses: 模型响应列表
            match_types: 匹配类型配置字典
            
        Returns:
            (汇总指标, 每个问题的指标字典)
        """
        total = len(responses)
        successful = [r for r in responses if r.success]
        failed = [r for r in responses if not r.success]

        # 存储每个问题的指标
        question_metrics: Dict[str, Dict[str, float]] = {}

        if not successful:
            return EvaluationMetrics(
                total_samples=total,
                successful_predictions=0,
                failed_predictions=total
            ), question_metrics

        # 获取各指标的配置
        exact_match_config = self._get_metric_config('calculate_exact_match', match_types)
        f1_score_config = self._get_metric_config('calculate_f1_score', match_types)
        semantic_sim_config = self._get_metric_config('calculate_semantic_similarity', match_types)
        coverage_config = self._get_metric_config('calculate_answer_coverage', match_types)
        relevance_config = self._get_metric_config('calculate_answer_relevance', match_types)
        utilization_config = self._get_metric_config('calculate_context_utilization', match_types)
        completeness_config = self._get_metric_config('calculate_completeness', match_types)
        conciseness_config = self._get_metric_config('calculate_conciseness', match_types)

        # 汇总指标列表
        exact_matches = []
        f1_scores = []
        semantic_sims = []
        inference_times = []
        coverages = []
        relevances = []
        utilizations = []
        completeness_scores = []
        conciseness_scores = []

        for resp in successful:
            pred = resp.predicted_answer
            truth = resp.ground_truth
            question = resp.question
            context = resp.context

            # 计算单个问题的所有指标
            single_metrics = self.calculator.compute_all_metrics_for_single(
                prediction=pred,
                question=question,
                context=context,
                ground_truth=truth,
                match_types=match_types
            )

            # 存储该问题的指标
            question_metrics[str(resp.question_id)] = {
                **single_metrics,
                'inference_time': resp.inference_time,
                'success': 1.0
            }

            # 添加到汇总列表
            exact_matches.append(single_metrics['exact_match'])
            f1_scores.append(single_metrics['f1_score'])
            semantic_sims.append(single_metrics['semantic_similarity'])
            inference_times.append(resp.inference_time)
            coverages.append(single_metrics['answer_coverage'])
            relevances.append(single_metrics['answer_relevance'])
            utilizations.append(single_metrics['context_utilization'])
            completeness_scores.append(single_metrics['answer_completeness'])
            conciseness_scores.append(single_metrics['answer_conciseness'])

        # 为失败的问题添加空指标
        for resp in failed:
            question_metrics[str(resp.question_id)] = {
                'exact_match': 0.0,
                'f1_score': 0.0,
                'semantic_similarity': 0.0,
                'answer_coverage': 0.0,
                'answer_relevance': 0.0,
                'context_utilization': 0.0,
                'answer_completeness': 0.0,
                'answer_conciseness': 0.0,
                'inference_time': 0.0,
                'success': 0.0,
                'error': resp.error_message
            }

        return EvaluationMetrics(
            total_samples=total,
            successful_predictions=len(successful),
            failed_predictions=len(failed),
            exact_match=np.mean(exact_matches),
            f1_score=np.mean(f1_scores),
            semantic_similarity=np.mean(semantic_sims),
            avg_inference_time=np.mean(inference_times),
            total_inference_time=np.sum(inference_times),
            answer_coverage=np.mean(coverages),
            answer_relevance=np.mean(relevances),
            context_utilization=np.mean(utilizations),
            answer_completeness=np.mean(completeness_scores),
            answer_conciseness=np.mean(conciseness_scores)
        ), question_metrics

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

    def get_best_worst_questions(
        self,
        agent_name: str,
        metric: str = 'f1_score',
        top_n: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        获取最佳和最差表现的问题
        
        Args:
            agent_name: Agent名称
            metric: 用于排序的指标名称
            top_n: 返回的问题数量
            
        Returns:
            {
                "best": [{question_id, question, metric_value, predicted, ground_truth}, ...],
                "worst": [{...}, ...]
            }
        """
        if agent_name not in self.results:
            logger.warning(f"Agent '{agent_name}' 的评估结果不存在")
            return {"best": [], "worst": []}

        result = self.results[agent_name]
        question_metrics = result.question_metrics

        if not question_metrics:
            logger.warning(f"Agent '{agent_name}' 没有问题级别的指标数据")
            return {"best": [], "worst": []}

        # 获取响应数据以便补充问题文本
        responses_map = {str(r.question_id): r for r in result.responses}

        # 构建可排序的问题列表
        scored_questions = []
        for qid, metrics in question_metrics.items():
            if metric in metrics:
                resp = responses_map.get(qid)
                if resp:
                    scored_questions.append({
                        'question_id': qid,
                        'question': resp.question,
                        'context': resp.context,
                        'metric_value': metrics[metric],
                        'predicted_answer': resp.predicted_answer,
                        'ground_truth': resp.ground_truth,
                        'inference_time': metrics.get('inference_time', 0),
                        'all_metrics': metrics
                    })

        # 排序
        scored_questions.sort(key=lambda x: x['metric_value'], reverse=True)

        return {
            'best': scored_questions[:top_n],
            'worst': scored_questions[-top_n:][::-1]  # 倒序，最差的是最后一个
        }


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

    # 5. 保存最终结果
    logger.info("步骤 5/6: 保存评估结果...")
    evaluator.save_results(detailed=True)

    # 6. 保存模型比较
    logger.info("步骤 6/6: 保存模型比较结果...")
    evaluator.save_comparison()

    logger.info("评估流程完成！")
    return evaluator.results


# 保持向后兼容的别名
APIAgentEvaluator = LLMEvaluator


if __name__ == "__main__":
    # 简单的测试代码
    print("评估系统已加载")
    print(f"模型目录: {MODELS_DIR}")
