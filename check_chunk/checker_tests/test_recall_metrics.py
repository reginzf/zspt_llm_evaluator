"""
切片召回质量评估测试
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from check_chunk.checkers import ChunkRecallEvaluator, RecallMetrics
from check_chunk.checker_funcs import (
    calculate_chunk_recall_metrics,
    calculate_batch_recall_metrics,
    get_precision_recall_f1,
    get_top_k_metrics,
    get_ranking_metrics
)


def test_basic_metrics():
    """测试基础指标计算"""
    print("=" * 60)
    print("测试基础指标计算")
    print("=" * 60)

    # 测试用例1：完美匹配
    retrieved = ["chunk_1", "chunk_2", "chunk_3"]
    relevant = ["chunk_1", "chunk_2", "chunk_3"]

    precision, recall, f1 = get_precision_recall_f1(retrieved, relevant)
    print(f"测试用例1 - 完美匹配:")
    print(f"  检索结果: {retrieved}")
    print(f"  相关文档: {relevant}")
    print(f"  准确率: {precision:.4f} (期望: 1.0000)")
    print(f"  召回率: {recall:.4f} (期望: 1.0000)")
    print(f"  F1分数: {f1:.4f} (期望: 1.0000)")
    assert abs(precision - 1.0) < 0.001
    assert abs(recall - 1.0) < 0.001
    assert abs(f1 - 1.0) < 0.001
    print("  ✓ 测试通过")

    # 测试用例2：部分匹配
    retrieved = ["chunk_1", "chunk_2", "chunk_3", "chunk_4"]
    relevant = ["chunk_2", "chunk_4", "chunk_6"]

    precision, recall, f1 = get_precision_recall_f1(retrieved, relevant)
    print(f"\n测试用例2 - 部分匹配:")
    print(f"  检索结果: {retrieved}")
    print(f"  相关文档: {relevant}")
    print(f"  准确率: {precision:.4f} (期望: 0.5000)")
    print(f"  召回率: {recall:.4f} (期望: 0.6667)")
    print(f"  F1分数: {f1:.4f} (期望: 0.5714)")
    assert abs(precision - 0.5) < 0.001
    assert abs(recall - 2 / 3) < 0.001
    assert abs(f1 - 0.5714) < 0.01
    print("  ✓ 测试通过")

    # 测试用例3：无匹配
    retrieved = ["chunk_1", "chunk_2", "chunk_3"]
    relevant = ["chunk_4", "chunk_5", "chunk_6"]

    precision, recall, f1 = get_precision_recall_f1(retrieved, relevant)
    print(f"\n测试用例3 - 无匹配:")
    print(f"  检索结果: {retrieved}")
    print(f"  相关文档: {relevant}")
    print(f"  准确率: {precision:.4f} (期望: 0.0000)")
    print(f"  召回率: {recall:.4f} (期望: 0.0000)")
    print(f"  F1分数: {f1:.4f} (期望: 0.0000)")
    assert abs(precision - 0.0) < 0.001
    assert abs(recall - 0.0) < 0.001
    assert abs(f1 - 0.0) < 0.001
    print("  ✓ 测试通过")


def test_top_k_metrics():
    """测试Top K指标"""
    print("\n" + "=" * 60)
    print("测试Top K指标")
    print("=" * 60)

    retrieved = ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
    relevant = ["chunk_2", "chunk_4", "chunk_6"]

    top_k_metrics = get_top_k_metrics(retrieved, relevant, k_values=[1, 2, 3, 5])

    print(f"检索结果: {retrieved}")
    print(f"相关文档: {relevant}")
    print("\nTop K指标:")

    expected_precision = {
        1: 0.0,  # 第一个不是相关文档
        2: 0.5,  # 第二个是相关文档，前2个中1个相关
        3: 0.3333,  # 前3个中1个相关
        5: 0.4  # 前5个中2个相关
    }

    expected_recall = {
        1: 0.0,  # 前1个中没有相关文档
        2: 0.3333,  # 前2个中命中1个相关文档，总共3个相关文档
        3: 0.3333,  # 前3个中命中1个相关文档
        5: 0.6667  # 前5个中命中2个相关文档
    }

    for k in [1, 2, 3, 5]:
        precision_k = top_k_metrics["precision_at_k"][k]
        recall_k = top_k_metrics["recall_at_k"][k]

        print(f"  @{k}:")
        print(f"    准确率: {precision_k:.4f} (期望: {expected_precision[k]:.4f})")
        print(f"    召回率: {recall_k:.4f} (期望: {expected_recall[k]:.4f})")

        assert abs(precision_k - expected_precision[k]) < 0.001
        assert abs(recall_k - expected_recall[k]) < 0.001

    print("  ✓ 所有Top K测试通过")


def test_ranking_metrics():
    """测试排序质量指标"""
    print("\n" + "=" * 60)
    print("测试排序质量指标")
    print("=" * 60)

    # 测试用例1：理想排序
    retrieved = ["chunk_2", "chunk_4", "chunk_1", "chunk_3", "chunk_5"]
    relevant = ["chunk_2", "chunk_4", "chunk_6"]

    ranking_metrics = get_ranking_metrics(retrieved, relevant)

    print(f"测试用例1 - 理想排序:")
    print(f"  检索结果: {retrieved}")
    print(f"  相关文档: {relevant}")

    # 计算期望值
    # AP: 第一个相关文档在位置1，第二个在位置2
    # precision@1 = 1/1 = 1.0, precision@2 = 2/2 = 1.0
    # AP = (1.0 + 1.0) / 2 = 1.0
    expected_ap = 1.0

    # NDCG: 增益序列 [1, 1, 0, 0, 0]
    # DCG = 1/log2(2) + 1/log2(3) ≈ 1 + 0.6309 = 1.6309
    # IDCG = 1/log2(2) + 1/log2(3) ≈ 1 + 0.6309 = 1.6309
    # NDCG = 1.0
    expected_ndcg = 1.0

    # MRR: 第一个相关文档在位置1，所以MRR = 1/1 = 1.0
    expected_mrr = 1.0

    print(f"  平均准确率: {ranking_metrics['average_precision']:.4f} (期望: {expected_ap:.4f})")
    print(f"  NDCG: {ranking_metrics['ndcg']:.4f} (期望: {expected_ndcg:.4f})")
    print(f"  MRR: {ranking_metrics['mrr']:.4f} (期望: {expected_mrr:.4f})")

    assert abs(ranking_metrics['average_precision'] - expected_ap) < 0.001
    assert abs(ranking_metrics['ndcg'] - expected_ndcg) < 0.001
    assert abs(ranking_metrics['mrr'] - expected_mrr) < 0.001
    print("  ✓ 测试通过")

    # 测试用例2：较差排序
    retrieved = ["chunk_1", "chunk_3", "chunk_5", "chunk_2", "chunk_4"]
    relevant = ["chunk_2", "chunk_4", "chunk_6"]

    ranking_metrics = get_ranking_metrics(retrieved, relevant)

    print(f"\n测试用例2 - 较差排序:")
    print(f"  检索结果: {retrieved}")
    print(f"  相关文档: {relevant}")

    # AP: 第一个相关文档在位置4，第二个在位置5
    # precision@4 = 1/4 = 0.25, precision@5 = 2/5 = 0.4
    # AP = (0.25 + 0.4) / 2 = 0.325
    expected_ap = 0.325

    # MRR: 第一个相关文档在位置4，所以MRR = 1/4 = 0.25
    expected_mrr = 0.25

    print(f"  平均准确率: {ranking_metrics['average_precision']:.4f} (期望: {expected_ap:.4f})")
    print(f"  MRR: {ranking_metrics['mrr']:.4f} (期望: {expected_mrr:.4f})")

    assert abs(ranking_metrics['average_precision'] - expected_ap) < 0.001
    assert abs(ranking_metrics['mrr'] - expected_mrr) < 0.001
    print("  ✓ 测试通过")


def test_full_metrics():
    """测试完整指标计算"""
    print("\n" + "=" * 60)
    print("测试完整指标计算")
    print("=" * 60)

    retrieved = ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
    relevant = ["chunk_2", "chunk_4", "chunk_6"]

    full_metrics = calculate_chunk_recall_metrics(retrieved, relevant)

    print(f"检索结果: {retrieved}")
    print(f"相关文档: {relevant}")
    print("\n完整指标:")

    # 验证关键指标
    assert "precision" in full_metrics
    assert "recall" in full_metrics
    assert "f1_score" in full_metrics
    assert "precision_at_k" in full_metrics
    assert "recall_at_k" in full_metrics
    assert "average_precision" in full_metrics
    assert "ndcg" in full_metrics
    assert "mrr" in full_metrics
    assert "hit_rate" in full_metrics
    assert "coverage" in full_metrics
    assert "redundancy" in full_metrics

    # 打印所有指标
    for key, value in full_metrics.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    @{k}: {v:.4f}")
        else:
            print(f"  {key}: {value}")

    print("\n  ✓ 所有指标计算正确")


def test_batch_evaluation():
    """测试批量评估"""
    print("\n" + "=" * 60)
    print("测试批量评估")
    print("=" * 60)

    queries_results = [
        (["chunk_1", "chunk_2", "chunk_3"], ["chunk_2", "chunk_4"]),
        (["chunk_4", "chunk_5", "chunk_6"], ["chunk_4", "chunk_6"]),
        (["chunk_7", "chunk_8"], ["chunk_7"]),
    ]

    batch_results = calculate_batch_recall_metrics(queries_results)

    print(f"查询数量: {batch_results['query_count']}")
    print(f"详细结果数量: {len(batch_results['detailed_results'])}")

    assert batch_results['query_count'] == 3
    assert len(batch_results['detailed_results']) == 3

    print("\n平均指标:")
    avg_metrics = batch_results['average_metrics']
    for key, value in avg_metrics.items():
        print(f"  {key}: {value:.4f}")

    print("\n详细结果:")
    for i, result in enumerate(batch_results['detailed_results']):
        print(f"  查询{i + 1}:")
        print(f"    检索数量: {result['retrieved_count']}")
        print(f"    相关数量: {result['relevant_count']}")
        print(f"    准确率: {result['metrics']['precision']:.4f}")
        print(f"    召回率: {result['metrics']['recall']:.4f}")

    print("\n  ✓ 批量评估测试通过")


def test_chunk_recall_evaluator():
    """测试ChunkRecallEvaluator类"""
    print("\n" + "=" * 60)
    print("测试ChunkRecallEvaluator类")
    print("=" * 60)

    # 创建评估器
    evaluator = ChunkRecallEvaluator(top_n_values=[1, 3, 5])

    # 测试数据
    retrieved = ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
    relevant = ["chunk_2", "chunk_4", "chunk_6"]

    # 计算指标
    metrics = evaluator.calculate_metrics(retrieved, relevant)

    print(f"检索结果: {retrieved}")
    print(f"相关文档: {relevant}")
    print(f"\n评估结果:\n{metrics}")

    # 验证指标类型
    assert isinstance(metrics, RecallMetrics)
    assert metrics.true_positives == 2
    assert metrics.false_positives == 3
    assert metrics.false_negatives == 1
    assert metrics.total_relevant == 3
    assert metrics.total_retrieved == 5

    # 测试top_n参数
    print(f"\n测试top_n参数 (top_n=3):")
    metrics_top3 = evaluator.calculate_metrics(retrieved, relevant, top_n=3)
    print(f"  只考虑前3个结果:")
    print(f"  准确率: {metrics_top3.precision:.4f}")
    print(f"  召回率: {metrics_top3.recall:.4f}")

    assert metrics_top3.total_retrieved == 3
    assert metrics_top3.true_positives == 1  # 只有chunk_2是相关的

    print("\n  ✓ ChunkRecallEvaluator测试通过")


def main():
    """主测试函数"""
    print("开始切片召回质量评估测试")
    print("=" * 60)

    try:
        test_basic_metrics()
        test_top_k_metrics()
        test_ranking_metrics()
        test_full_metrics()
        test_batch_evaluation()
        test_chunk_recall_evaluator()

        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
