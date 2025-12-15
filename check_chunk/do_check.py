from src.lzpt_ls_operate import login_zlpt, login_label_studio
from label_studio.task import get_tasks_with_specific_choice
from check_chunk.checker_funcs import calculate_chunk_recall_metrics
from zlpt.api.knowledge_base.retriveve import Retrieve
from utils.logger import logger
from utils.pub_funs import save_json_file
import jsonpath
from env_config_init import QUESTION_JSON, REPORT_PATH


def cal_metric_all(project_name, kno_id, search_type):
    """
    获取指定search_type的召回和label studio下已标注的数据，计算metric
    :param project_name: 在label studio上的项目名称
    :param kno_id: 在紫鸾知识平台上的知识库id
    :param search_type: 搜索类型，可选值为 vectorSearch(向量检索) | hybridSearch(混合检索) | augmentedSearch(增强检索)
    :return:
    """
    logger.info(f"开始获取项目[{project_name}]的切片数据，知识ID:[{kno_id}]，搜索类型:[{search_type}]")
    # 登录
    zlpt_user = login_zlpt()
    ls_user = login_label_studio()
    retrieve_client = Retrieve(zlpt_user)
    project = ls_user.get_projects(title=project_name)[0]
    logger.debug(f"成功获取项目: {project.title}")
    # 要保存的文件名称
    file_path = REPORT_PATH / f'metric_{search_type}.json'
    # 获取json中的问题
    questions = []
    metric_all = {}
    for qs in jsonpath.jsonpath(QUESTION_JSON, '$..datas..questions'):
        questions.extend(qs)

    logger.info(f"共找到 {len(questions)} 个问题需要处理")

    # 为每个问题获取切片
    for question in questions:
        logger.debug(f"正在处理问题: {question}")

        # 获取知识平台的切片
        zlpt_retrieve_data = retrieve_client.webKnowledgeRetrieve(search_type, question, kno_id)
        zlpt_records_count = len(zlpt_retrieve_data.get('data', {}).get('records', []))
        logger.debug(f"从知识平台获取到 {zlpt_records_count} 个切片，问题: {question}")

        # 获取ls中标注过的数据
        labeled_tasks = get_tasks_with_specific_choice(project, question)
        logger.debug(f"从Label Studio获取到 {len(labeled_tasks)} 个已标注任务，问题: {question}")

        # 由于chunk_id一样，直接提取chunk_id
        zlpt_retrieve_data_chunk_ids = jsonpath.jsonpath(zlpt_retrieve_data, '$.data.records..chunk_id')
        labeled_tasks_chunk_ids = [task['data']['chunk_id'] for task in labeled_tasks]

        logger.debug(
            f"提取到知识平台切片ID数量: {len(zlpt_retrieve_data_chunk_ids)}, 已标注切片ID数量: {len(labeled_tasks_chunk_ids)}")

        # 直接使用chunk_id计算切片质量
        metrics = calculate_chunk_recall_metrics(labeled_tasks_chunk_ids, zlpt_retrieve_data_chunk_ids)
        metric_all[question] = metrics

        logger.info(f"问题 [{question}] 的切片质量计算结果: {metrics}")

        save_json_file(metric_all, file_path)
        logger.info(f"所有问题的切片质量指标已保存至 {file_path} 文件")


if __name__ == '__main__':
    project_name = 'OSPFv2_600_0'
    kno_id = 'KLB_a0020070fdca41dbb25eee3a543fc3aa'
    cal_metric_all(project_name, kno_id, 'vectorSearch')
