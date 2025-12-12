"""
切片召回质量评估模块
用于计算切片召回的各种质量指标，包括召回率、准确率、top K等
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from dataclasses import dataclass
from enum import Enum
CHUNK_KEY_MAP = {
    "precision": "精确率",
    "recall": "召回率",
    "f1_score": "F1分数",
    "precision_at_k": "K值精确率",
    "recall_at_k": "K值召回率",
    "average_precision": "平均精确率",
    "mean_average_precision": "平均精确率均值",
    "ndcg": "归一化折损累计增益",
    "mrr": "平均倒数排名",
    "hit_rate": "命中率",
    "coverage": "覆盖率",
    "redundancy": "冗余度",
    "true_positives": "真正例",
    "false_positives": "假正例",
    "false_negatives": "假负例",
    "total_relevant": "总相关文档数",
    "total_retrieved": "总检索文档数"
}


class MetricType(Enum):
    """评估指标类型"""
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    PRECISION_AT_K = "precision_at_k"
    RECALL_AT_K = "recall_at_k"
    MAP = "map"
    NDCG = "ndcg"
    MRR = "mrr"
    HIT_RATE = "hit_rate"


@dataclass
class RecallMetrics:
    """召回质量指标结果"""
    # 基础指标
    precision: float
    recall: float
    f1_score: float
    
    # Top K指标
    precision_at_k: Dict[int, float]  # 不同K值下的准确率
    recall_at_k: Dict[int, float]     # 不同K值下的召回率
    
    # 排序质量指标
    average_precision: float          # 平均准确率
    mean_average_precision: float     # 平均准确率均值（当有多个查询时）
    ndcg: float                       # 归一化折损累计增益
    mrr: float                        # 平均倒数排名
    
    # 其他指标
    hit_rate: float                   # 命中率
    coverage: float                   # 覆盖率
    redundancy: float                 # 冗余度
    
    # 详细统计
    true_positives: int               # 真正例
    false_positives: int              # 假正例
    false_negatives: int              # 假反例
    total_relevant: int               # 总相关文档数
    total_retrieved: int              # 总检索文档数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "average_precision": self.average_precision,
            "mean_average_precision": self.mean_average_precision,
            "ndcg": self.ndcg,
            "mrr": self.mrr,
            "hit_rate": self.hit_rate,
            "coverage": self.coverage,
            "redundancy": self.redundancy,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "total_relevant": self.total_relevant,
            "total_retrieved": self.total_retrieved,
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"RecallMetrics(\n"
            f"  Precision: {self.precision:.4f}, Recall: {self.recall:.4f}, F1: {self.f1_score:.4f}\n"
            f"  AP: {self.average_precision:.4f}, NDCG: {self.ndcg:.4f}, MRR: {self.mrr:.4f}\n"
            f"  Hit Rate: {self.hit_rate:.4f}, Coverage: {self.coverage:.4f}\n"
            f"  TP: {self.true_positives}, FP: {self.false_positives}, FN: {self.false_negatives}\n"
            f")"
        )


class ChunkRecallEvaluator:
    """
    切片召回质量评估器
    
    用于计算切片召回的各种质量指标，包括：
    1. 基础指标：准确率、召回率、F1分数
    2. Top K指标：不同K值下的准确率和召回率
    3. 排序质量指标：平均准确率、NDCG、MRR
    4. 其他指标：命中率、覆盖率、冗余度
    """
    
    def __init__(self, top_n_values: List[int] = None):
        """
        初始化评估器
        
        Args:
            top_n_values: 要计算的Top K值列表，默认为[1, 3, 5, 10]
        """
        if top_n_values is None:
            top_n_values = [1, 3, 5, 10]
        self.top_n_values = top_n_values
    
    def calculate_metrics(
        self,
        retrieved_chunks: List[str],
        relevant_chunks: List[str],
        top_n: Optional[int] = None
    ) -> RecallMetrics:
        """
        计算召回质量指标
        
        Args:
            retrieved_chunks: 本次提问召回的切片ID列表
            relevant_chunks: 标记为对应问题回答的切片ID列表
            top_n: 如果指定，只考虑前top_n个结果
            
        Returns:
            RecallMetrics: 包含所有评估指标的结果对象
        """
        # 如果指定了top_n，只取前top_n个结果
        if top_n is not None and top_n > 0:
            retrieved_chunks = retrieved_chunks[:top_n]
        
        # 转换为集合便于计算
        retrieved_set = set(retrieved_chunks)
        relevant_set = set(relevant_chunks)
        
        # 计算基础统计
        true_positives = len(retrieved_set & relevant_set)
        false_positives = len(retrieved_set - relevant_set)
        false_negatives = len(relevant_set - retrieved_set)
        total_relevant = len(relevant_set)
        total_retrieved = len(retrieved_set)
        
        # 计算基础指标
        precision = self._calculate_precision(true_positives, total_retrieved)
        recall = self._calculate_recall(true_positives, total_relevant)
        f1_score = self._calculate_f1_score(precision, recall)
        
        # 计算Top K指标
        precision_at_k = self._calculate_precision_at_k(retrieved_chunks, relevant_set)
        recall_at_k = self._calculate_recall_at_k(retrieved_chunks, relevant_set)
        
        # 计算排序质量指标
        average_precision = self._calculate_average_precision(retrieved_chunks, relevant_set)
        ndcg = self._calculate_ndcg(retrieved_chunks, relevant_set)
        mrr = self._calculate_mrr(retrieved_chunks, relevant_set)
        
        # 计算其他指标
        hit_rate = self._calculate_hit_rate(retrieved_chunks, relevant_set)
        coverage = self._calculate_coverage(retrieved_set, relevant_set)
        redundancy = self._calculate_redundancy(retrieved_chunks)
        
        return RecallMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            average_precision=average_precision,
            mean_average_precision=average_precision,  # 单查询时MAP=AP
            ndcg=ndcg,
            mrr=mrr,
            hit_rate=hit_rate,
            coverage=coverage,
            redundancy=redundancy,
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            total_relevant=total_relevant,
            total_retrieved=total_retrieved,
        )
    
    def _calculate_precision(self, true_positives: int, total_retrieved: int) -> float:
        """计算准确率"""
        if total_retrieved == 0:
            return 0.0
        return true_positives / total_retrieved
    
    def _calculate_recall(self, true_positives: int, total_relevant: int) -> float:
        """计算召回率"""
        if total_relevant == 0:
            return 0.0
        return true_positives / total_relevant
    
    def _calculate_f1_score(self, precision: float, recall: float) -> float:
        """计算F1分数"""
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)
    
    def _calculate_precision_at_k(
        self, 
        retrieved_chunks: List[str], 
        relevant_set: set
    ) -> Dict[int, float]:
        """计算不同K值下的准确率"""
        precision_at_k = {}
        
        for k in self.top_n_values:
            if k <= 0:
                continue
            
            # 取前k个结果
            top_k = retrieved_chunks[:min(k, len(retrieved_chunks))]
            top_k_set = set(top_k)
            
            # 计算准确率@k
            relevant_in_top_k = len(top_k_set & relevant_set)
            precision_k = relevant_in_top_k / len(top_k) if len(top_k) > 0 else 0.0
            precision_at_k[k] = precision_k
        
        return precision_at_k
    
    def _calculate_recall_at_k(
        self, 
        retrieved_chunks: List[str], 
        relevant_set: set
    ) -> Dict[int, float]:
        """计算不同K值下的召回率"""
        recall_at_k = {}
        total_relevant = len(relevant_set)
        
        if total_relevant == 0:
            for k in self.top_n_values:
                recall_at_k[k] = 0.0
            return recall_at_k
        
        for k in self.top_n_values:
            if k <= 0:
                continue
            
            # 取前k个结果
            top_k = retrieved_chunks[:min(k, len(retrieved_chunks))]
            top_k_set = set(top_k)
            
            # 计算召回率@k
            relevant_in_top_k = len(top_k_set & relevant_set)
            recall_k = relevant_in_top_k / total_relevant
            recall_at_k[k] = recall_k
        
        return recall_at_k
    
    def _calculate_average_precision(
        self, 
        retrieved_chunks: List[str], 
        relevant_set: set
    ) -> float:
        """计算平均准确率（Average Precision）"""
        if not relevant_set:
            return 0.0
        
        relevant_count = 0
        precision_sum = 0.0
        
        for i, chunk_id in enumerate(retrieved_chunks, 1):
            if chunk_id in relevant_set:
                relevant_count += 1
                precision_at_i = relevant_count / i
                precision_sum += precision_at_i
        
        if relevant_count == 0:
            return 0.0
        
        return precision_sum / relevant_count
    
    def _calculate_ndcg(
        self, 
        retrieved_chunks: List[str], 
        relevant_set: set
    ) -> float:
        """计算归一化折损累计增益（NDCG）"""
        if not retrieved_chunks:
            return 0.0
        
        # 假设相关文档的增益为1，不相关为0
        gains = [1.0 if chunk_id in relevant_set else 0.0 for chunk_id in retrieved_chunks]
        
        # 计算DCG
        dcg = 0.0
        for i, gain in enumerate(gains, 1):
            dcg += gain / np.log2(i + 1)
        
        # 计算理想DCG（IDCG）
        ideal_gains = sorted(gains, reverse=True)
        idcg = 0.0
        for i, gain in enumerate(ideal_gains, 1):
            idcg += gain / np.log2(i + 1)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def _calculate_mrr(
        self, 
        retrieved_chunks: List[str], 
        relevant_set: set
    ) -> float:
        """计算平均倒数排名（MRR）"""
        if not relevant_set:
            return 0.0
        
        for i, chunk_id in enumerate(retrieved_chunks, 1):
            if chunk_id in relevant_set:
                return 1.0 / i
        
        return 0.0
    
    def _calculate_hit_rate(
        self, 
        retrieved_chunks: List[str], 
        relevant_set: set
    ) -> float:
        """计算命中率（至少命中一个相关文档的概率）"""
        if not retrieved_chunks:
            return 0.0
        
        for chunk_id in retrieved_chunks:
            if chunk_id in relevant_set:
                return 1.0
        
        return 0.0
    
    def _calculate_coverage(
        self, 
        retrieved_set: set, 
        relevant_set: set
    ) -> float:
        """计算覆盖率（检索到的相关文档占所有相关文档的比例）"""
        if not relevant_set:
            return 0.0
        
        covered = len(retrieved_set & relevant_set)
        return covered / len(relevant_set)
    
    def _calculate_redundancy(self, retrieved_chunks: List[str]) -> float:
        """计算冗余度（重复文档的比例）"""
        if len(retrieved_chunks) <= 1:
            return 0.0
        
        unique_chunks = set(retrieved_chunks)
        total_chunks = len(retrieved_chunks)
        unique_count = len(unique_chunks)
        
        if total_chunks == 0:
            return 0.0
        
        return 1.0 - (unique_count / total_chunks)
    
    def evaluate_batch(
        self,
        queries_results: List[Tuple[List[str], List[str]]],
        top_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批量评估多个查询的结果
        
        Args:
            queries_results: 列表，每个元素为(retrieved_chunks, relevant_chunks)的元组
            top_n: 如果指定，只考虑前top_n个结果
            
        Returns:
            Dict: 包含平均指标和详细结果的字典
        """
        if not queries_results:
            return {
                "average_metrics": None,
                "detailed_results": [],
                "query_count": 0
            }
        
        detailed_results = []
        metrics_list = []
        
        for retrieved_chunks, relevant_chunks in queries_results:
            metrics = self.calculate_metrics(retrieved_chunks, relevant_chunks, top_n)
            detailed_results.append({
                "retrieved_count": len(retrieved_chunks),
                "relevant_count": len(relevant_chunks),
                "metrics": metrics.to_dict()
            })
            metrics_list.append(metrics)
        
        # 计算平均指标
        avg_metrics = self._calculate_average_metrics(metrics_list)
        
        return {
            "average_metrics": avg_metrics,
            "detailed_results": detailed_results,
            "query_count": len(queries_results)
        }
    
    def _calculate_average_metrics(self, metrics_list: List[RecallMetrics]) -> Dict[str, float]:
        """计算平均指标"""
        if not metrics_list:
            return {}
        
        # 初始化累加器
        sums = {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "average_precision": 0.0,
            "ndcg": 0.0,
            "mrr": 0.0,
            "hit_rate": 0.0,
            "coverage": 0.0,
            "redundancy": 0.0,
        }
        
        # 累加所有指标
        for metrics in metrics_list:
            sums["precision"] += metrics.precision
            sums["recall"] += metrics.recall
            sums["f1_score"] += metrics.f1_score
            sums["average_precision"] += metrics.average_precision
            sums["ndcg"] += metrics.ndcg
            sums["mrr"] += metrics.mrr
            sums["hit_rate"] += metrics.hit_rate
            sums["coverage"] += metrics.coverage
            sums["redundancy"] += metrics.redundancy
        
        # 计算平均值
        count = len(metrics_list)
        avg_metrics = {key: value / count for key, value in sums.items()}
        
        # 计算平均准确率均值（MAP）
        avg_metrics["mean_average_precision"] = sums["average_precision"] / count
        
        return avg_metrics


# 使用示例
def main():
    """使用示例"""
    # 创建评估器
    evaluator = ChunkRecallEvaluator(top_n_values=[1, 3, 5, 10])
    
    # 示例数据
    retrieved_chunks = ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
    relevant_chunks = ["chunk_2", "chunk_4", "chunk_6"]
    
    # 计算单个查询的指标
    metrics = evaluator.calculate_metrics(retrieved_chunks, relevant_chunks)
    print("单个查询评估结果:")
    print(metrics)
    print("\n详细指标:")
    for key, value in metrics.to_dict().items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    @{k}: {v:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # 批量评估示例
    print("\n" + "="*50)
    print("批量评估示例:")
    
    queries_results = [
        (["chunk_1", "chunk_2", "chunk_3"], ["chunk_2", "chunk_4"]),
        (["chunk_4", "chunk_5", "chunk_6"], ["chunk_4", "chunk_6"]),
        (["chunk_7", "chunk_8"], ["chunk_7"]),
    ]
    
    batch_results = evaluator.evaluate_batch(queries_results)
    print(f"查询数量: {batch_results['query_count']}")
    print("\n平均指标:")
    for key, value in batch_results["average_metrics"].items():
        print(f"  {key}: {value:.4f}")


if __name__ == "__main__":
    main()