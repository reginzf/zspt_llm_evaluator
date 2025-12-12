from src.lzpt_ls_operate import *
from label_studio.task import get_tasks_with_specific_choice
from check_chunk.checker_funcs import calculate_chunk_recall_metrics
from check_chunk.checkers.ChunkRecallMetrics import CHUNK_KEY_MAP


def main():
    """
     主函数：执行完整的流程包括知识库创建、文件上传、切片获取和Label Studio项目初始化
     """
    # 上传文件并解析，获取切片数据并标注
    # knowledge_dict, zlpt_user, ls_user, kno_id, project = zlpt_init_and_ls_label()
    from check_chunk.do_check import get_chunk_all
    get_chunk_all('OSPFv2_600_0', 'KLB_a0020070fdca41dbb25eee3a543fc3aa', 'vectorSearch')


if __name__ == '__main__':
    # from src.lzpt_ls_operate import zlpt_init_and_ls_label
    # zlpt_init_and_ls_label()
    main()
