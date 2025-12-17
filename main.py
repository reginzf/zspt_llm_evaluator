from src.lzpt_ls_operate import *
from env_config_init import KNOWLEDGE_PATH,REPORT_PATH
from utils.pub_funs import load_json_file


def main():
    """
     主函数：执行完整的流程包括知识库创建、文件上传、切片获取和Label Studio项目初始化
     """
    # step 1：上传文件并解析，获取切片数据并标注
    knowledge_dict, zlpt_user, ls_user, kno_id, project = zlpt_init_and_ls_label()

    # step 2: 标注 知识平台召回标注 | 本地模型预测标注 | llm模型预测标注 三选一
    # 初始化项目标注器

    from check_chunk.do_check import cal_metric_all
    # 需要读取的字典文件
    knowledge_dict = load_json_file(KNOWLEDGE_PATH)
    # knowledge_dict = {'kno_id': 'KLB_a0020070fdca41dbb25eee3a543fc3aa', 'name': 'OSPFv2_600_0', 'chunk_size': 600,
    #                   'chunk_overlap': 0}

    project_name = knowledge_dict['name']
    kno_id = knowledge_dict['kno_id']
    for search_type in ["vectorSearch", "hybridSearch", "augmentedSearch"]:
        # 计算指标
        cal_metric_all(project_name, kno_id, search_type)
    # 生成报告
    from reports.reports_funcs.generate_report import generate_reports_from_metric_files
    generate_reports_from_metric_files(REPORT_PATH)

if __name__ == '__main__':
    # from src.lzpt_ls_operate import zlpt_init_and_ls_label
    # zlpt_init_and_ls_label()
    main()
