from zlpt.api.base_client import BaseClient


class Retrieve(BaseClient):
    def webKnowledgeRetrieve(self, search_type, content, knowledgeId):
        """
        :param search_type: 搜索类型，可选值为 vectorSearch(向量检索) | hybridSearch(混合检索) | augmentedSearch(增强检索)
        :param content: 问题
        :param knowledgeId: 知识库ID
        :return:{"msg": null, "code": 200, "data": {"records": [
            {"contentCode": "caa32c33af6f48c5a410b5d9ac8f2c61", "chunk_size": 485, "fileName": "OSPFv2.txt",
             "doc_title": "OSPFv2.txt", "catalog": "ospf_chunk_500",
             "downloadUrl": "https://slzzptwx.uniscity.com:20443/zlzspt/minio/zlzspt/e5c8479c-d37c-43c8-b21a-10d7d64b8c2e/KLB_d82ed57fe20e42668712a4bfb1d41c14/20251203160843011.txt",
             "description": null, "abstract_text": "", "knowledgeId": "KLB_d82ed57fe20e42668712a4bfb1d41c14", "score": 0.91992,
             "metaData": "{\"tags\": []}", "doc_name": "OSPFv2", "knowledge_name": "ospf_chunk_500", "chunk_position": 247,
             "doc_available": "1", "updateTime": "2025-12-03 16:08:55", "doc_id": "DOC_c9c4f8e410f042b6a0b34df6cc8788d3",
             "chunk_text": "下文与(OSPFv2.txt)有关。\n。\n\n     DC位：\n\n     该位描述了按［引用21］的说明处理按需链路。\n\nA.3 OSPF包格式\n     有五种不同的OSPF包类型。所有的OSPF包都以24个字节的头部开始。首先描述包头，而后描述各种类型。在本节中列出包中的各域，并列举出各域的定义。\n\n     所有的OSPF包（除了OSPFHello包）都处理LSA列表。例如，LSU包实现在OSPF路由域中洪泛LSA。因此，必须理解LSA的格式才能分析OSPF协议包。LSA的格式在附录A.4中描述。\n\n     接收及处理OSPF包的细节见第8.2节。发送OSPF包的解释见第8.1节。\n\nA.3.1 OSPF包头\n     每个OSPF包都以24字节的头部开始。头部所包含的所有信息用于决定包如何进行下一步操作。这在本规范的第8.2节中定义。\n\n     版本号/Version#：\n\n     OSPF的版本号，本规范所说明的协议版本号为2。\n\n     类型/Type：\n\n     OSPF包的类型按如下定义。具体细节见附录A.3.2到附录A.3.6",
             "chunk_id": "4b579144d01f11f0ac8502a65fdc6d6a", "question_text": "", "chunk_available": "1", "doc_source": "0",
             "fileSize": "203.98KB", "page_index": 1, "knowledge_id": "KLB_d82ed57fe20e42668712a4bfb1d41c14", "chunk_title": "",
             "fileFormat": "txt"},
            ]}}
        """
        api = f'api/zspt/zsgl/webKnowledgeRetrieve/{search_type}'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, content=content, knowledgeId=knowledgeId)
        return res



