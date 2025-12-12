from label_studio.task import get_tasks_with_specific_choice
from zlpt.api.knowledge_base import  Retrieve
from checkers.chunk_checkers import calculate_chunk_recall_metrics

def question_metrics(project, question_context):
    labeled_tasks = get_tasks_with_specific_choice(project, '在广播网络中，OSPF路由器如何发现邻居？')
    # 获取问题切片
    retrieve_client = Retrieve(zlpt_user)
    zlpt_retrieve_data = retrieve_client.webKnowledgeRetrieve('vectorSearch', '在广播网络中，OSPF路由器如何发现邻居？',
                                                              kno_id)
    # 由于chunk_id一样，直接提取chunk_id
    labeled_tasks_chunk_ids = [task['data']['chunk_id'] for task in labeled_tasks]
    zlpt_retrieve_data_chunk_ids = jsonpath.jsonpath(zlpt_retrieve_data, '$.data.records..chunk_id')
    # 直接使用chunk_id计算切片质量
    metrics = calculate_chunk_recall_metrics(labeled_tasks_chunk_ids, zlpt_retrieve_data_chunk_ids)
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"  {CHUNK_KEY_MAP[key]}:")
            for k, v in value.items():
                print(f"    @{k}: {v:.4f}")
        else:
            print(f"  {CHUNK_KEY_MAP[key]}: {value}")