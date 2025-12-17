"""
切片召回质量评估接口
提供简洁的API用于计算切片召回的各种质量指标
"""

from typing import List, Dict, Any, Tuple, Optional
from check_chunk.checkers.ChunkRecallMetrics import ChunkRecallEvaluator
from env_config_init import settings

evaluator = ChunkRecallEvaluator(top_n_values=settings.TOP_K)


def calculate_chunk_recall_metrics(
        retrieved_chunks: List[str],
        relevant_chunks: List[str],
        top_n: Optional[int] = None,
) -> Dict[str, Any]:
    """
    计算切片召回质量指标（简化接口）
    
    Args:
        retrieved_chunks: 本次提问召回的切片ID列表
        relevant_chunks: 标记为对应问题回答的切片ID列表
        top_n: 如果指定，只考虑前top_n个结果
    Returns:
        Dict: 包含所有评估指标的字典
    """
    metrics = evaluator.calculate_metrics(retrieved_chunks, relevant_chunks, top_n)
    return metrics.to_dict()


def calculate_similarity_recall_metrics(
        matched_list: List[float],
        len_relevant_chunks: int,
        threshold: float = 0.5,
        top_n: Optional[int] = None,
) -> Dict[str, Any]:
    """
    根据相似度匹配列表计算切片召回质量指标

    Args:
        matched_list: 匹配分数列表，1表示完全匹配，0表示没有匹配，小数表示相似度
                    例如: [1, 0, 0.911, 1, 0, 0.611, 0]
        len_relevant_chunks: 对应问题标注的切片数量
        threshold: 判断为相关文档的阈值，默认0.5
        top_n: 如果指定，只考虑前top_n个结果
        top_k_values: 要计算的Top K值列表，默认为[1, 3, 5, 10]

    Returns:
        Dict: 包含所有评估指标的字典
    """
    metrics = evaluator.calculate_metrics_by_matched_list(
        matched_list,
        len_relevant_chunks,
        threshold,
        top_n
    )
    return metrics.to_dict()


def calculate_batch_recall_metrics(
        queries_results: List[Tuple[List[str], List[str]]],
        top_n: Optional[int] = None
) -> Dict[str, Any]:
    """
    批量计算切片召回质量指标
    
    Args:
        queries_results: 列表，每个元素为(retrieved_chunks, relevant_chunks)的元组
        top_n: 如果指定，只考虑前top_n个结果
        top_k_values: 要计算的Top K值列表，默认为[1, 3, 5, 10]
        
    Returns:
        Dict: 包含平均指标和详细结果的字典
    """
    return evaluator.evaluate_batch(queries_results, top_n)


def calculate_batch_similarity_metrics(scores_queries: List[Tuple[List[float], str]],
                                   threshold: float = 0.5,
                                   len_chunk2_list: Optional[List[int]] = None,
                                   top_n: Optional[int] = None):
    return evaluator.evaluate_scores_batch(scores_queries, threshold, len_chunk2_list, top_n)


def get_precision_recall_f1(
        retrieved_chunks: List[str],
        relevant_chunks: List[str],
        top_n: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    快速获取准确率、召回率和F1分数
    
    Args:
        retrieved_chunks: 本次提问召回的切片ID列表
        relevant_chunks: 标记为对应问题回答的切片ID列表
        top_n: 如果指定，只考虑前top_n个结果
        
    Returns:
        Tuple[float, float, float]: (准确率, 召回率, F1分数)
    """
    evaluator = ChunkRecallEvaluator()
    metrics = evaluator.calculate_metrics(retrieved_chunks, relevant_chunks, top_n)
    return metrics.precision, metrics.recall, metrics.f1_score


def get_top_k_metrics(
        retrieved_chunks: List[str],
        relevant_chunks: List[str],
        k_values: List[int] = None
) -> Dict[str, Dict[int, float]]:
    """
    获取Top K指标
    
    Args:
        retrieved_chunks: 本次提问召回的切片ID列表
        relevant_chunks: 标记为对应问题回答的切片ID列表
        k_values: K值列表，默认为[1, 3, 5, 10]
        
    Returns:
        Dict: 包含precision@k和recall@k的字典
    """
    if k_values is None:
        k_values = [1, 3, 5, 10]

    evaluator = ChunkRecallEvaluator(top_n_values=k_values)
    metrics = evaluator.calculate_metrics(retrieved_chunks, relevant_chunks)

    return {
        "precision_at_k": metrics.precision_at_k,
        "recall_at_k": metrics.recall_at_k
    }


def get_ranking_metrics(
        retrieved_chunks: List[str],
        relevant_chunks: List[str]
) -> Dict[str, float]:
    """
    获取排序质量指标
    
    Args:
        retrieved_chunks: 本次提问召回的切片ID列表
        relevant_chunks: 标记为对应问题回答的切片ID列表
        
    Returns:
        Dict: 包含AP、NDCG、MRR的字典
    """
    evaluator = ChunkRecallEvaluator()
    metrics = evaluator.calculate_metrics(retrieved_chunks, relevant_chunks)

    return {
        "average_precision": metrics.average_precision,
        "ndcg": metrics.ndcg,
        "mrr": metrics.mrr
    }


# 使用示例
if __name__ == "__main__":
    # 示例数据
    retrieved = ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
    relevant = ["chunk_2", "chunk_4", "chunk_6"]

    print("1. 基础指标:")
    precision, recall, f1 = get_precision_recall_f1(retrieved, relevant)
    print(f"   准确率: {precision:.4f}")
    print(f"   召回率: {recall:.4f}")
    print(f"   F1分数: {f1:.4f}")

    print("\n2. Top K指标:")
    top_k_metrics = get_top_k_metrics(retrieved, relevant)
    for metric_name, values in top_k_metrics.items():
        print(f"   {metric_name}:")
        for k, value in values.items():
            print(f"     @{k}: {value:.4f}")

    print("\n3. 排序质量指标:")
    ranking_metrics = get_ranking_metrics(retrieved, relevant)
    for metric_name, value in ranking_metrics.items():
        print(f"   {metric_name}: {value:.4f}")

    print("\n4. 完整指标:")
    full_metrics = calculate_chunk_recall_metrics(retrieved, relevant)
    for key, value in full_metrics.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"     @{k}: {v:.4f}")
        else:
            print(f"   {key}: {value}")

    print("\n5. 相似度匹配指标:")
    # 示例相似度匹配列表
    matched_list = [1, 0, 0.911, 1, 0, 0.611, 0]
    len_relevant_chunks = 6  # 假设标注了6个相关切片
    similarity_metrics = calculate_similarity_recall_metrics(
        matched_list,
        len_relevant_chunks,
        threshold=0.5
    )
    for key, value in similarity_metrics.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"     @{k}: {v:.4f}")
        else:
            print(f"   {key}: {value}")
