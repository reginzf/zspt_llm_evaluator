from src.core.api.base_client import BaseClient


class Retrieve(BaseClient):
    def webKnowledgeRetrieve(self, search_type, content, knowledgeId):
        """
        :param search_type: vectorSearch(向量检索) hybridSearch（混合检索） augmentedSearch（增强检索）
        :param content:问题
        :param knowledgeId:知识库ID
        :return:
        """
        api = f'api/zspt/zsgl/webKnowledgeRetrieve/{search_type}'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, content=content, knowledgeId=knowledgeId)
        return res


