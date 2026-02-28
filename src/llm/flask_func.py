"""
给后端flask调用的功能方法
"""
import logging
from typing import Dict, Any, Optional
from env_config_init import PROJECT_ROOT
from src.llm.api_agent_evaluator import LLMEvaluator, run_evaluation
from src.utils.pub_funs import read_json_file

# 配置日志记录器
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_match_types_from_config(config_path: str) -> Optional[Dict[str, Any]]:
    """
    从配置文件中加载 match_types 配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        match_types 配置字典，如果不存在则返回 None
    """
    try:
        config = read_json_file(config_path, default={})
        match_types = config.get('match_types')
        if match_types:
            logger.info(f"从配置文件加载 match_types 成功")
            return match_types
        return None
    except Exception as e:
        logger.warning(f"从配置文件加载 match_types 失败: {e}")
        return None


def basic_evaluation(question_set_path: str, agent_config_path, output_dir="tests/evaluation_results", sample_size=None,
                     parallel=False, max_workers=1, retry_attempts=1, match_types: Optional[Dict[str, Any]] = None):
    """
    使用便捷函数评价单个模型
    
    Args:
        question_set_path: 问答对数据集路径
        agent_config_path: Agent配置文件路径
        output_dir: 输出目录
        sample_size: 采样数量
        parallel: 是否并行处理
        max_workers: 并行工作线程数
        retry_attempts: 重试次数
        match_types: 匹配类型配置字典，如果为None则从配置文件读取
            格式: {
                "calculate_exact_match": {"match_type": "normalized"},
                "calculate_f1_score": {"cal_type": "word"},
                ...
            }
    """
    try:
        # 如果未传入 match_types，尝试从配置文件读取
        if match_types is None and agent_config_path:
            match_types = load_match_types_from_config(str(PROJECT_ROOT / agent_config_path))
        
        # 使用便捷函数进行评估
        results = run_evaluation(
            qa_source=str(PROJECT_ROOT / question_set_path),
            config_path=str(PROJECT_ROOT / agent_config_path),
            output_dir=str(PROJECT_ROOT / output_dir),
            sample_size=sample_size,
            parallel=parallel,
            max_workers=max_workers,
            retry_attempts=retry_attempts,
            match_types=match_types
        )

        logger.info("评估完成！")
        logger.info(f"评估的模型数量: {len(results)}")

        # 显示结果概要
        for model_name, result in results.items():
            metrics = result.metrics
            logger.info(f"\n模型: {model_name}")
            logger.info(f"  精确匹配: {metrics.exact_match:.4f}")
            logger.info(f"  F1分数: {metrics.f1_score:.4f}")
            logger.info(f"  成功率: {metrics.successful_predictions}/{metrics.total_samples}")

    except FileNotFoundError as e:
        logger.error(f"文件未找到错误: {e}")
        logger.error("请确保数据集和配置文件路径正确")
    except Exception as e:
        logger.error(f"评估过程中出现错误: {e}")


def create_evaluator(output_dir: str) -> LLMEvaluator:
    return LLMEvaluator(output_dir=output_dir)


def load_question_pairs(evaluator: LLMEvaluator, qa_source_path: str) -> LLMEvaluator:
    evaluator.load_qa_pairs(qa_source_path)
    return evaluator


def load_llm_agent(evaluator, config_path, agents_config):
    """
    运行完整评估流程的便捷函数

    Args:
        evaluator：LLMEvaluator实例
        config_path: Agent配置文件路径
        agents_config: 直接传入的Agent配置列表

    Returns:
        LLMEvaluator实例
    """
    evaluator.load_agents_from_config(config_path, agents_config)
    if not evaluator.agents:
        logger.error("没有可用的Agent，评估终止")
        return False
    return evaluator


def run_evaluator(evaluator, sample_size, parallel, max_workers, retry_attempts):
    evaluator.evaluate_all(
        sample_size=sample_size,
        parallel=parallel,
        max_workers=max_workers,
        retry_attempts=retry_attempts
    )


def demonstrate_custom_agent():
    """演示自定义Agent的添加"""
    logger.info("\n=== 自定义Agent示例 ===")

    try:
        evaluator = LLMEvaluator(output_dir="./evaluation_results_custom")

        # 添加自定义Agent配置
        custom_agent_config = {
            "name": "My-Custom-Agent",
            "type": "custom",
            "api_key": "your-api-key-here",
            "api_url": "https://your-api-endpoint.com/chat",
            "request_template": {
                "prompt": "基于以下内容回答问题：\n\n内容：{context}\n\n问题：{question}",
                "temperature": 0.1,
                "max_tokens": 200
            },
            "response_parser": "lambda x: x.get('response', '') if isinstance(x, dict) else str(x)",
            "timeout": 30
        }

        success, message = evaluator.add_agent(custom_agent_config, test_connection=False)
        if success:
            logger.info(f"✓ 自定义Agent添加成功: {message}")
        else:
            logger.error(f"✗ 自定义Agent添加失败: {message}")

    except Exception as e:
        logger.error(f"添加自定义Agent时出错: {e}")


def show_available_features():
    """展示可用的功能和配置选项"""
    logger.info("\n=== LLM评估系统可用功能详解 ===\n")

    logger.info("【核心评估器方法 - LLMEvaluator类】")
    logger.info("1. __init__(output_dir) - 初始化评估器")
    logger.info("   参数: output_dir (str) - 结果输出目录")
    logger.info("   功能: 创建评估器实例，初始化输出目录")

    logger.info("\n2. load_qa_pairs(source, source_type, split) - 加载问答对数据")
    logger.info("   参数: source (str) - 数据源路径")
    logger.info("         source_type (str) - 数据源类型 (auto/hf_dataset/json/jsonl)")
    logger.info("         split (str) - 数据集分割 (test/validation/train)")
    logger.info("   返回: List[QuestionAnswerPair] - 问答对列表")
    logger.info("   功能: 支持多种数据格式加载问答对数据")

    logger.info("\n3. load_agents_from_config(config_path, agents_config) - 从配置加载Agents")
    logger.info("   参数: config_path (str) - 配置文件路径")
    logger.info("         agents_config (List[Dict]) - 直接传入的Agent配置列表")
    logger.info("   返回: Dict[str, Tuple[bool, str]] - 连通性测试结果")
    logger.info("   功能: 批量加载Agent配置并测试连接")

    logger.info("\n4. add_agent(agent_config, test_connection) - 动态添加单个Agent")
    logger.info("   参数: agent_config (Dict) - Agent配置字典")
    logger.info("         test_connection (bool) - 是否测试连通性")
    logger.info("   返回: Tuple[bool, str] - (是否成功, 消息)")
    logger.info("   功能: 动态添加新的Agent配置")

    logger.info("\n5. evaluate_single(agent_name, qa_pair, retry_attempts, retry_delay) - 评估单个问答对")
    logger.info("   参数: agent_name (str) - Agent名称")
    logger.info("         qa_pair (QuestionAnswerPair) - 问答对")
    logger.info("         retry_attempts (int) - 重试次数")
    logger.info("         retry_delay (float) - 重试间隔（秒）")
    logger.info("   返回: ModelResponse - 模型响应")
    logger.info("   功能: 对单个问答对进行推理评估")

    logger.info(
        "\n6. evaluate_agent(agent_name, sample_size, parallel, max_workers, retry_attempts, show_progress) - 评估单个Agent")
    logger.info("   参数: agent_name (str) - Agent名称")
    logger.info("         sample_size (int) - 采样数量")
    logger.info("         parallel (bool) - 是否并行处理")
    logger.info("         max_workers (int) - 并行工作线程数")
    logger.info("         retry_attempts (int) - 重试次数")
    logger.info("         show_progress (bool) - 是否显示进度条")
    logger.info("   返回: ModelEvaluationResult - 评估结果")
    logger.info("   功能: 对指定Agent进行全面评估")

    logger.info("\n7. evaluate_all(sample_size, parallel, max_workers, retry_attempts, show_progress) - 评估所有Agent")
    logger.info("   参数: 同evaluate_agent方法")
    logger.info("   返回: Dict[str, ModelEvaluationResult] - 所有Agent的评估结果")
    logger.info("   功能: 批量评估所有已配置的Agent")

    logger.info("\n8. save_results(filename, detailed) - 保存评估结果")
    logger.info("   参数: filename (str) - 文件名")
    logger.info("         detailed (bool) - 是否保存详细信息")
    logger.info("   功能: 将评估结果保存为JSON文件")

    logger.info("\n9. save_intermediate_results(agent_name, responses) - 保存中间结果")
    logger.info("   参数: agent_name (str) - Agent名称")
    logger.info("         responses (List[ModelResponse]) - 响应列表")
    logger.info("   功能: 保存评估过程中的中间结果")

    logger.info("\n10. compare_models() - 比较所有模型表现")
    logger.info("    返回: Dict - 模型比较结果")
    logger.info("    功能: 生成多模型性能对比分析")

    logger.info("\n11. save_comparison(filename) - 保存模型比较结果")
    logger.info("    参数: filename (str) - 文件名")
    logger.info("    功能: 将模型比较结果保存为JSON文件")

    logger.info("\n12. generate_report(agent_name) - 生成评估报告")
    logger.info("    参数: agent_name (str) - 指定Agent名称")
    logger.info("    返回: str - 报告文本")
    logger.info("    功能: 生成详细的文本格式评估报告")

    logger.info("\n13. save_report(agent_name, filename) - 保存评估报告")
    logger.info("    参数: agent_name (str) - 指定Agent名称")
    logger.info("          filename (str) - 文件名")
    logger.info("    功能: 将评估报告保存到文件")

    logger.info("\n【便捷函数】")
    logger.info("run_evaluation() - 运行完整评估流程的便捷函数")
    logger.info("   功能: 一站式完成从数据加载到结果保存的完整流程")

    logger.info("\n【支持的Agent类型】")
    logger.info("- deepseek: DeepSeek API")
    logger.info("- openai: OpenAI API")
    logger.info("- custom: 自定义API")

    logger.info("\n【评估指标体系】")
    logger.info("准确性指标:")
    logger.info("  - 精确匹配 (Exact Match)")
    logger.info("  - F1分数")
    logger.info("  - 部分匹配")
    logger.info("  - 语义相似度")

    logger.info("\n知识库能力指标:")
    logger.info("  - 答案覆盖率")
    logger.info("  - 答案相关性")
    logger.info("  - 上下文利用率")
    logger.info("  - 答案完整性")
    logger.info("  - 答案简洁性")

    logger.info("\n效率指标:")
    logger.info("  - 平均推理时间")
    logger.info("  - 总推理时间")

    logger.info("\n【数据集支持格式】")
    logger.info("- HuggingFace数据集目录")
    logger.info("- JSON文件")
    logger.info("- JSONL文件")

    logger.info("\n【配置文件示例】")
    logger.info("请参考 configs/agent_config_example.json")


def main():
    qs_path = r'D:\pyworkplace\git_place\ai-ken\tests\my_datasets\hf_mirrors-google_xtreme'
    agent_config_path = r'D:\pyworkplace\git_place\ai-ken\configs\agent_config.json'
    output_dir = r'D:\pyworkplace\git_place\ai-ken\tests\evaluation_results'
    basic_evaluation(qs_path, agent_config_path, output_dir=output_dir, sample_size=30, )


if __name__ == "__main__":
    main()
    # show_available_features()
