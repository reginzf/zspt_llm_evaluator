from checkers.chunk_checkers import CorrespondenceChecker, PositionBasedCorrespondenceChecker, \
    SemanticCorrespondenceChecker


def main():
    from zlpt.login import LoginManager
    from env_config_init import settings
    # 登录紫光云平台
    login_manager = LoginManager(settings.ZLPT_BASE_URL)
    login_manager.login(settings.USERNAME, settings.PASSWORD, settings.DOMAIN)
    login_manager.get_auth_key()
    # 获取知识库id
    from zlpt.api.knowledge_base.knowledgeBase import KnowledgeBase
    knowledge_base = KnowledgeBase(login_manager)
    knowledge_base_infos = knowledge_base.knowledge_list('ospf')['data']
    # 获取知识库的问题切片
    from zlpt.api.knowledge_base.retriveve import Retrieve
    from utils.zl_to_label_studio import retrieve_format_for_label_studio
    retrieve = Retrieve(login_manager)
    chunk_res = []
    for base in knowledge_base_infos:
        knowledge_id = base['knowledgeId']
        knowledge_name = base['knowledgeName']
        knowledge_slices = \
            retrieve.webKnowledgeRetrieve('augmentedSearch', "ospf有哪些报文类型", knowledge_id)['data'][
                'records']
        # 转化为label studio格式
        chunk_res.append(retrieve_format_for_label_studio(knowledge_slices))
        # 获取doc的切片
    # 进行比较
    original_text = open(r'/tests/ospf/context/OSPFv2.txt', 'r').read()
    correspondence_checker = CorrespondenceChecker(original_text)
    postion_checker = PositionBasedCorrespondenceChecker()
    semantic_checker = SemanticCorrespondenceChecker()

    print(correspondence_checker.check_content_overlap_correspondence(chunk_res[0], chunk_res[1]))
    print(postion_checker.check_position_correspondence(chunk_res[0], chunk_res[1], original_text))
    print(semantic_checker.check_semantic_correspondence(chunk_res[0], chunk_res[1]))


if __name__ == '__main__':
    main()
