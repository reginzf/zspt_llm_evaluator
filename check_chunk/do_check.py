from src.lzpt_ls_operate import *
from label_studio.task import get_tasks_with_specific_choice
from check_chunk.checker_funcs import calculate_chunk_recall_metrics


def get_chunk_all(project_name, kno_id, search_type):
    zlpt_user = login_zlpt()
    ls_user = login_label_studio()
    retrieve_client = Retrieve(zlpt_user)
    project = ls_user.get_projects(title=project_name)[0]
    # 获取json中的问题
    questions = []
    metric_all = {}
    for qs in jsonpath.jsonpath(QUESTION_JSON, '$..datas..questions'):
        questions.extend(qs)
    # 为每个问题获取切片
    for question in questions:
        # 获取知识平台的切片
        zlpt_retrieve_data = retrieve_client.webKnowledgeRetrieve(search_type, question, kno_id)
        # 获取ls中标注过的数据
        labeled_tasks = get_tasks_with_specific_choice(project, question)
        # 由于chunk_id一样，直接提取chunk_id
        zlpt_retrieve_data_chunk_ids = jsonpath.jsonpath(zlpt_retrieve_data, '$.data.records..chunk_id')
        labeled_tasks_chunk_ids = [task['data']['chunk_id'] for task in labeled_tasks]
        # 直接使用chunk_id计算切片质量
        metrics = calculate_chunk_recall_metrics(labeled_tasks_chunk_ids, zlpt_retrieve_data_chunk_ids)
        metric_all[question] = metrics
    save_json_file(metric_all, 'metric_all.json')

