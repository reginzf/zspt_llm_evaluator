from src.lzpt_ls_operate import *
from label_studio.task import get_tasks_with_specific_choice
from checkers.chunk_checkers import calculate_chunk_recall_metrics, CHUNK_KEY_MAP

#
# def main():
#     """
#      主函数：执行完整的流程包括知识库创建、文件上传、切片获取和Label Studio项目初始化
#      """
#     # 上传文件并解析，获取切片数据并标注
#     # knowledge_dict, zlpt_user, ls_user, kno_id, project = zlpt_init_and_ls_label()
#     zlpt_user = login_zlpt()
#     ls_user = login_label_studio()
#     project = ls_user.get_projects(title='OSPFv2_RFC2328_Detailed_600_10')[0]
#     kno_id = 'KLB_089b5bc846ee46d6ae5adc3637bcc9f5'
#     # todo 手动过一遍切片标注
#     # todo 比较不同chunk_size的召回结果
#     # 获取标注过的数据
#     labeled_tasks = get_tasks_with_specific_choice(project, '在广播网络中，OSPF路由器如何发现邻居？')
#     # 获取问题切片
#     retrieve_client = Retrieve(zlpt_user)
#     zlpt_retrieve_data = retrieve_client.webKnowledgeRetrieve('vectorSearch', '在广播网络中，OSPF路由器如何发现邻居？',
#                                                               kno_id)
#     # 由于chunk_id一样，直接提取chunk_id
#     labeled_tasks_chunk_ids = [task['data']['chunk_id'] for task in labeled_tasks]
#     zlpt_retrieve_data_chunk_ids = jsonpath.jsonpath(zlpt_retrieve_data, '$.data.records..chunk_id')
#     # 直接使用chunk_id计算切片质量
#     metrics = calculate_chunk_recall_metrics(labeled_tasks_chunk_ids, zlpt_retrieve_data_chunk_ids)
#     for key, value in metrics.items():
#         if isinstance(value, dict):
#             print(f"  {CHUNK_KEY_MAP[key]}:")
#             for k, v in value.items():
#                 print(f"    @{k}: {v:.4f}")
#         else:
#             print(f"  {CHUNK_KEY_MAP[key]}: {value}")
#

if __name__ == '__main__':
    from src.lzpt_ls_operate import zlpt_init_and_ls_label
    zlpt_init_and_ls_label()
