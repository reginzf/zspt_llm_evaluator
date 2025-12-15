from src.lzpt_ls_operate import *
from label_studio.task import get_tasks_with_specific_choice
from check_chunk.checker_funcs import calculate_chunk_recall_metrics
from utils.logger import logger


def get_chunk_all(project_name, kno_id, search_type):
    logger.info(f"开始获取项目[{project_name}]的切片数据，知识ID:[{kno_id}]，搜索类型:[{search_type}]")
    
    zlpt_user = login_zlpt()
    ls_user = login_label_studio()
    retrieve_client = Retrieve(zlpt_user)
    project = ls_user.get_projects(title=project_name)[0]
    
    logger.debug(f"成功获取项目: {project.title}")
    
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
        
        logger.debug(f"提取到知识平台切片ID数量: {len(zlpt_retrieve_data_chunk_ids)}, 已标注切片ID数量: {len(labeled_tasks_chunk_ids)}")
        
        # 直接使用chunk_id计算切片质量
        metrics = calculate_chunk_recall_metrics(labeled_tasks_chunk_ids, zlpt_retrieve_data_chunk_ids)
        metric_all[question] = metrics
        
        logger.info(f"问题 [{question}] 的切片质量计算结果: {metrics}")
    
    save_json_file(metric_all, 'metric_all.json')
    logger.info("所有问题的切片质量指标已保存至 metric_all.json 文件")

