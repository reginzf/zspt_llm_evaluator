import json
import numpy as np
from typing import List, Dict, Tuple, Set
from collections import defaultdict
import hashlib
import random


class SliceConsistencyTester:
    """
    切片生成内部一致性测试工具
    用于评估切片分类机器人的内部一致性
    """

    def __init__(self, config_path: str = None):
        """
        初始化测试器

        Args:
            config_path: 配置文件路径，包含问题分类信息
        """
        self.question_map = {}
        self.question_list = []
        self.type_mapping = {}

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str):
        """
        加载配置文件

        Args:
            config_path: JSON配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 构建问题映射
        question_idx = 0
        for category in config["datas"]:
            cat_type = category["type"]
            questions = category["questions"]

            self.question_map[cat_type] = {
                "questions": questions,
                "indices": list(range(question_idx, question_idx + len(questions)))
            }

            # 建立全局索引映射
            for i, q in enumerate(questions):
                self.question_list.append(q)
                self.type_mapping[question_idx + i] = cat_type

            question_idx += len(questions)

    def generate_test_cases(self, num_cases: int = 10) -> List[Dict]:
        """
        生成内部一致性测试用例

        Args:
            num_cases: 生成的测试用例数量

        Returns:
            测试用例列表
        """
        test_cases = []

        # 1. 同义替换测试用例
        test_cases.extend(self._generate_synonym_cases(num_cases // 3))

        # 2. 表述变换测试用例
        test_cases.extend(self._generate_paraphrase_cases(num_cases // 3))

        # 3. 片段组合测试用例
        test_cases.extend(self._generate_combination_cases(num_cases // 3))

        # 4. 边界条件测试用例
        test_cases.extend(self._generate_boundary_cases(3))

        return test_cases

    def _generate_synonym_cases(self, num_cases: int) -> List[Dict]:
        """
        生成同义替换测试用例

        Args:
            num_cases: 测试用例数量

        Returns:
            同义替换测试用例列表
        """
        cases = []

        # OSPF相关同义词映射
        ospf_synonyms = {
            "Router ID": ["路由器标识符", "路由标识", "路由器ID", "RID"],
            "32位": ["32比特", "32-bit", "32位长度", "32位宽度"],
            "字节": ["byte", "字节数", "字节长度"],
            "Hello报文": ["Hello包", "Hello消息", "Hello数据包"],
            "LSA": ["链路状态通告", "链路状态广告", "Link State Advertisement"],
            "LSDB": ["链路状态数据库", "链路状态库", "Link State Database"],
            "邻居": ["邻接路由器", "相邻路由器", "neighbor"],
            "邻接关系": ["邻接", "adjacency", "邻接状态"]
        }

        # 基础文本模板
        base_texts = [
            "OSPF中Router ID的长度是32位",
            "OSPF报文头部长度是24字节",
            "OSPF通过Hello报文发现邻居",
            "LSA用于传播链路状态信息",
            "LSDB存储网络拓扑信息"
        ]

        for i in range(min(num_cases, len(base_texts))):
            base_text = base_texts[i]

            # 生成同义替换版本
            paraphrased = base_text
            for original, synonyms in ospf_synonyms.items():
                if original in paraphrased:
                    synonym = random.choice(synonyms)
                    paraphrased = paraphrased.replace(original, synonym)

            cases.append({
                "test_type": "synonym_replacement",
                "original": base_text,
                "variant": paraphrased,
                "expected_consistency": "high",  # 期望高度一致
                "description": f"同义替换测试: {base_text} -> {paraphrased}"
            })

        return cases

    def _generate_paraphrase_cases(self, num_cases: int) -> List[Dict]:
        """
        生成表述变换测试用例

        Args:
            num_cases: 测试用例数量

        Returns:
            表述变换测试用例列表
        """
        cases = []

        # 表述变换模板
        paraphrase_templates = [
            # 主动变被动
            ("OSPF路由器使用Hello报文发现邻居", "邻居通过Hello报文被OSPF路由器发现"),

            # 陈述变疑问
            ("Router ID的长度是32位", "Router ID是多少位？答案是32位"),

            # 详细变简洁
            ("OSPF协议中的链路状态数据库用于存储整个区域的网络拓扑信息", "LSDB存储网络拓扑"),

            # 拆分表述
            ("OSPF有Hello、DBD、LSR、LSU、LSAck五种报文类型",
             "OSPF报文类型包括Hello报文。还有DBD报文。以及LSR、LSU和LSAck报文。"),

            # 合并表述
            ("Hello报文用于发现邻居。DBD报文用于同步数据库。", "Hello和DBD报文分别用于发现邻居和同步数据库。")
        ]

        for i in range(min(num_cases, len(paraphrase_templates))):
            original, paraphrased = paraphrase_templates[i]

            cases.append({
                "test_type": "paraphrase",
                "original": original,
                "variant": paraphrased,
                "expected_consistency": "high",
                "description": f"表述变换测试: {original[:30]}..."
            })

        return cases

    def _generate_combination_cases(self, num_cases: int) -> List[Dict]:
        """
        生成片段组合测试用例

        Args:
            num_cases: 测试用例数量

        Returns:
            片段组合测试用例列表
        """
        cases = []

        # 基础片段
        fragments = [
            "OSPF Router ID是32位",
            "用于唯一标识路由器",
            "在区域内必须唯一",
            "通常配置为Loopback接口IP"
        ]

        # 生成组合测试
        for i in range(min(num_cases, 5)):
            # 随机选择2-3个片段
            selected = random.sample(fragments, random.randint(2, 3))

            # 创建不同组合方式
            combined1 = "。".join(selected)  # 句号连接
            combined2 = "，".join(selected)  # 逗号连接
            combined3 = " ".join(selected)  # 空格连接

            cases.append({
                "test_type": "fragment_combination",
                "original": combined1,
                "variant": combined2,
                "expected_consistency": "high",
                "description": f"片段组合测试: {len(selected)}个片段的不同连接方式"
            })

            cases.append({
                "test_type": "fragment_combination",
                "original": combined1,
                "variant": combined3,
                "expected_consistency": "high",
                "description": f"片段组合测试: {len(selected)}个片段的不同连接方式"
            })

        return cases

    def _generate_boundary_cases(self, num_cases: int) -> List[Dict]:
        """
        生成边界条件测试用例

        Args:
            num_cases: 测试用例数量

        Returns:
            边界条件测试用例列表
        """
        cases = []

        # 边界测试用例
        boundary_cases = [
            # 空文本
            ("", "OSPF Router ID是32位", "low"),

            # 单字符
            ("A", "OSPF Router ID是32位", "low"),

            # 完全无关
            ("今天天气很好", "OSPF Router ID是32位", "low"),

            # 部分相关
            ("网络协议", "OSPF是一种网络路由协议", "medium"),

            # 包含数字但不相关
            ("32位系统", "OSPF Router ID是32位", "low"),
        ]

        for i in range(min(num_cases, len(boundary_cases))):
            text1, text2, expected = boundary_cases[i]

            cases.append({
                "test_type": "boundary",
                "original": text1,
                "variant": text2,
                "expected_consistency": expected,
                "description": f"边界测试: '{text1[:10]}...' vs '{text2[:10]}...'"
            })

        return cases

    def run_consistency_test(self, classifier_func, test_cases: List[Dict] = None) -> Dict:
        """
        运行一致性测试

        Args:
            classifier_func: 切片分类函数，接收文本返回匹配结果
            test_cases: 测试用例列表，如果为None则自动生成

        Returns:
            测试结果字典
        """
        if test_cases is None:
            test_cases = self.generate_test_cases()

        results = {
            "test_cases": [],
            "summary": {
                "total_cases": 0,
                "passed_cases": 0,
                "failed_cases": 0,
                "consistency_scores": [],
                "by_test_type": defaultdict(list)
            }
        }

        for test_case in test_cases:
            # 获取两个版本的预测结果
            pred1 = classifier_func(test_case["original"])
            pred2 = classifier_func(test_case["variant"])

            # 计算一致性分数
            consistency_score = self._calculate_consistency_score(pred1, pred2)

            # 判断是否通过
            expected = test_case["expected_consistency"]
            passed = self._evaluate_consistency(consistency_score, expected)

            # 记录结果
            case_result = {
                **test_case,
                "predictions_original": pred1,
                "predictions_variant": pred2,
                "consistency_score": consistency_score,
                "passed": passed
            }

            results["test_cases"].append(case_result)

            # 更新统计信息
            results["summary"]["total_cases"] += 1
            if passed:
                results["summary"]["passed_cases"] += 1
            else:
                results["summary"]["failed_cases"] += 1

            results["summary"]["consistency_scores"].append(consistency_score)
            results["summary"]["by_test_type"][test_case["test_type"]].append({
                "score": consistency_score,
                "passed": passed
            })

        # 计算总体统计
        results["summary"]["pass_rate"] = (
            results["summary"]["passed_cases"] / results["summary"]["total_cases"]
            if results["summary"]["total_cases"] > 0 else 0
        )

        results["summary"]["avg_consistency"] = np.mean(results["summary"]["consistency_scores"])
        results["summary"]["std_consistency"] = np.std(results["summary"]["consistency_scores"])

        return results

    def _calculate_consistency_score(self, pred1: List, pred2: List) -> float:
        """
        计算两个预测结果的一致性分数

        Args:
            pred1: 第一个预测结果
            pred2: 第二个预测结果

        Returns:
            一致性分数 (0-1)
        """
        if not pred1 and not pred2:
            return 1.0  # 两个都为空，完全一致

        if not pred1 or not pred2:
            return 0.0  # 一个为空一个不为空，完全不一致

        # 使用Jaccard相似度
        set1 = set(self._flatten_predictions(pred1))
        set2 = set(self._flatten_predictions(pred2))

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _flatten_predictions(self, predictions: List) -> List[str]:
        """
        扁平化预测结果

        Args:
            predictions: 预测结果列表

        Returns:
            扁平化的预测标识列表
        """
        flattened = []
        for pred in predictions:
            if isinstance(pred, dict) and "type" in pred and "questions" in pred:
                cat_type = pred["type"]
                for q_idx in pred["questions"]:
                    flattened.append(f"{cat_type}_{q_idx}")
        return flattened

    def _evaluate_consistency(self, score: float, expected: str) -> bool:
        """
        根据一致性分数和期望等级判断是否通过

        Args:
            score: 一致性分数 (0-1)
            expected: 期望的一致性等级

        Returns:
            是否通过测试
        """
        thresholds = {
            "high": 0.8,  # 高度一致：分数 > 0.8
            "medium": 0.5,  # 中等一致：分数 > 0.5
            "low": 0.2  # 低度一致：分数 < 0.3
        }

        if expected == "high":
            return score > thresholds["high"]
        elif expected == "medium":
            return thresholds["medium"] < score <= thresholds["high"]
        elif expected == "low":
            return score < thresholds["low"]
        else:
            return score > 0.5  # 默认阈值

    def generate_report(self, results: Dict, output_path: str = None) -> str:
        """
        生成测试报告

        Args:
            results: 测试结果
            output_path: 输出文件路径

        Returns:
            报告文本
        """
        report_lines = []

        # 标题
        report_lines.append("=" * 60)
        report_lines.append("切片分类机器人内部一致性测试报告")
        report_lines.append("=" * 60)
        report_lines.append("")

        # 总体统计
        summary = results["summary"]
        report_lines.append("【总体统计】")
        report_lines.append(f"测试用例总数: {summary['total_cases']}")
        report_lines.append(f"通过用例数: {summary['passed_cases']}")
        report_lines.append(f"失败用例数: {summary['failed_cases']}")
        report_lines.append(f"通过率: {summary['pass_rate']:.2%}")
        report_lines.append(f"平均一致性分数: {summary['avg_consistency']:.3f}")
        report_lines.append(f"一致性分数标准差: {summary['std_consistency']:.3f}")
        report_lines.append("")

        # 按测试类型统计
        report_lines.append("【按测试类型统计】")
        for test_type, type_results in summary["by_test_type"].items():
            scores = [r["score"] for r in type_results]
            passed = sum(1 for r in type_results if r["passed"])
            total = len(type_results)

            report_lines.append(f"  {test_type}:")
            report_lines.append(f"    用例数: {total}")
            report_lines.append(f"    通过数: {passed}")
            report_lines.append(f"    通过率: {passed / total:.2%}" if total > 0 else "    通过率: N/A")
            report_lines.append(f"    平均分数: {np.mean(scores):.3f}" if scores else "    平均分数: N/A")
        report_lines.append("")

        # 失败用例详情
        failed_cases = [case for case in results["test_cases"] if not case["passed"]]
        if failed_cases:
            report_lines.append("【失败用例详情】")
            for i, case in enumerate(failed_cases[:10], 1):  # 只显示前10个
                report_lines.append(f"{i}. {case['description']}")
                report_lines.append(f"   原始文本: {case['original'][:50]}...")
                report_lines.append(f"   变体文本: {case['variant'][:50]}...")
                report_lines.append(f"   一致性分数: {case['consistency_score']:.3f}")
                report_lines.append(f"   期望等级: {case['expected_consistency']}")
                report_lines.append("")

        # 建议
        report_lines.append("【改进建议】")
        if summary["pass_rate"] > 0.9:
            report_lines.append("✓ 系统一致性表现优秀")
        elif summary["pass_rate"] > 0.7:
            report_lines.append("✓ 系统一致性表现良好，可进一步优化边界情况")
        elif summary["pass_rate"] > 0.5:
            report_lines.append("⚠ 系统一致性一般，建议检查同义替换和表述变换的处理")
        else:
            report_lines.append("✗ 系统一致性较差，需要重新设计匹配算法")

        report_text = "\n".join(report_lines)

        # 输出到文件
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)

        return report_text

    def visualize_results(self, results: Dict, save_path: str = None):
        """
        可视化测试结果（需要matplotlib）

        Args:
            results: 测试结果
            save_path: 保存图片路径
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            # 设置样式
            sns.set_style("whitegrid")
            plt.figure(figsize=(12, 8))

            # 1. 一致性分数分布
            plt.subplot(2, 2, 1)
            scores = results["summary"]["consistency_scores"]
            plt.hist(scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            plt.axvline(x=0.8, color='red', linestyle='--', label='高一致性阈值')
            plt.axvline(x=0.5, color='orange', linestyle='--', label='中一致性阈值')
            plt.xlabel('一致性分数')
            plt.ylabel('频数')
            plt.title('一致性分数分布')
            plt.legend()

            # 2. 测试类型表现
            plt.subplot(2, 2, 2)
            type_data = results["summary"]["by_test_type"]
            types = list(type_data.keys())
            avg_scores = [
                np.mean([r["score"] for r in type_data[t]])
                for t in types
            ]

            colors = ['lightcoral', 'lightgreen', 'lightblue', 'gold']
            bars = plt.bar(types, avg_scores, color=colors[:len(types)])
            plt.xlabel('测试类型')
            plt.ylabel('平均一致性分数')
            plt.title('各测试类型表现')

            # 在柱子上添加数值
            for bar, score in zip(bars, avg_scores):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                         f'{score:.3f}', ha='center', va='bottom')

            # 3. 通过率饼图
            plt.subplot(2, 2, 3)
            summary = results["summary"]
            labels = ['通过', '失败']
            sizes = [summary['passed_cases'], summary['failed_cases']]
            colors = ['lightgreen', 'lightcoral']
            explode = (0.1, 0) if sizes[0] > sizes[1] else (0, 0.1)

            plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                    autopct='%1.1f%%', shadow=True, startangle=90)
            plt.axis('equal')
            plt.title(f'总体通过率: {summary["pass_rate"]:.1%}')

            # 4. 分数随时间变化（按测试顺序）
            plt.subplot(2, 2, 4)
            test_sequence = range(len(scores))
            plt.plot(test_sequence, scores, marker='o', linestyle='-', color='blue', alpha=0.6)
            plt.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='高一致性')
            plt.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='中一致性')
            plt.xlabel('测试用例序号')
            plt.ylabel('一致性分数')
            plt.title('一致性分数变化趋势')
            plt.legend()
            plt.ylim(0, 1.1)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"图表已保存至: {save_path}")

            plt.show()

        except ImportError:
            print("警告: 需要安装matplotlib和seaborn进行可视化")
            print("安装命令: pip install matplotlib seaborn")


# 使用示例
def example_usage():
    """
    使用示例
    """
    # 1. 初始化测试器
    tester = SliceConsistencyTester(r'/tests/ospf/ospfv2_detailed_questions.json')

    # 2. 模拟一个分类函数（实际使用时替换为你的分类函数）
    def mock_classifier(text: str) -> List[Dict]:
        """
        模拟分类函数 - 实际使用时替换为你的实现
        """
        # 这里模拟一个简单的关键词匹配
        predictions = []

        # 检查每种类型的问题
        question_types = ["factual", "contextual", "conceptual", "reasoning", "application"]

        for q_type in question_types:
            matched_indices = []

            # 简单关键词匹配（实际应该用更复杂的语义匹配）
            if "Router ID" in text and "32" in text and q_type == "factual":
                matched_indices.append(0)
            elif "Hello" in text and "邻居" in text and q_type == "contextual":
                matched_indices.append(0)
            elif "LSA" in text and q_type == "conceptual":
                matched_indices.append(0)

            if matched_indices:
                predictions.append({
                    "type": q_type,
                    "questions": matched_indices
                })
        print(predictions)
        return predictions

    # 3. 运行测试
    print("正在运行内部一致性测试...")
    results = tester.run_consistency_test(mock_classifier)

    # 4. 生成报告
    report = tester.generate_report(results, "consistency_test_report.txt")
    print(report)

    # 5. 可视化结果（可选）
    try:
        tester.visualize_results(results, "consistency_test_visualization.png")
    except:
        print("跳过可视化（依赖库未安装）")

if __name__ == '__main__':
    example_usage()

