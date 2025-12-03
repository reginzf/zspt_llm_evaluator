from src.core.api.base_client import BaseClient
import math


class KnowledgeBasePage(BaseClient):
    def knowledge_page_list(self, knowledgeId, docName, docSource="0,1,2", current=1, size=10):
        """
        查询指定知识库下的文件列表
        :param knowledgeId:
        :param docName:
        :param docSource:
        :param current:
        :param size:
        :return: {"code": 200, "msg": null, "data":
        {"records": [{"id": "34515", "knowledgeId": "KLB_f1b895e57a3e4851939483e11f84ee6a",
                     "docId": "DOC_d61cdd48e2c845aabcf436bce49eba8d", "docName": "ospf",
                     "importFileType": null, "filePath": null, "fileName": null,
                     "fileFormat": "html", "fileSize": null, "docStatus": null,
                     "tagStatus": 1, "studyStatus": 1, "msg": "学习成功",
                     "createTime": "2025-12-01 10:55:16",
                     "updateTime": "2025-12-02 22:06:29", "attachId": null,
                     "docSource": "1",
                     "htmlUrl": "https://info.support.huawei.com/info-finder/encyclopedia/zh/OSPF.html",
                     "description": null, "syncPeriod": null, "metaData": "{\"tags\": []}",
                     "automaticMetaData": null, "augmentedStatus": "3",
                     "summaryStatus": null, "metaAssociateMethod": null}],
        "total": 1,"size": 10, "current": 1, "pages": 1}, "ok": true}
        """
        api = f'api/zspt/zsgl/knowledgeBaseContent/page'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, knowledgeId=knowledgeId, docName=docName, docSource=docSource,
                                current=current, size=size)
        return res

    def doc_detail(self, docId):
        """
        获取指定doc的属性
        :param docId:
        :return: {"code": 200, "msg": null, "data": {
                "document": {"id": "34515", "knowledgeId": "KLB_f1b895e57a3e4851939483e11f84ee6a", "description": null,
                             "docId": "DOC_d61cdd48e2c845aabcf436bce49eba8d", "docName": "ospf",
                             "contentCode": "bd2ce09bd9f641e19867bfea4aa7c251", "importFileType": null, "fileName": "ospf",
                             "fileFormat": "html", "filePath": null, "fileSize": null, "md5Value": null, "compressFileName": null,
                             "compressFolder": null, "uploadTime": null, "sliceNum": 80, "docDataSize": 25498,
                             "postCode": "759df20dc1824a1aa95588c197177638", "msg": "学习成功", "docStatus": null, "studyStatus": 1,
                             "creator": null, "creatorUserName": "nrgtest", "creatorRealName": null, "updateUserName": null,
                             "updateRealName": null, "createTime": "2025-12-01 10:55:16", "updateTime": "2025-12-03 10:38:01",
                             "metaData": "{\"tags\": []}", "automaticMetaData": null, "attachId": null, "delFlag": null,
                             "thirdPartyId": null, "thirdPartyPath": null, "augmentedStatus": null, "tagStatus": "1",
                             "docSource": null, "htmlUrl": null, "connectorCode": null, "summaryMethod": "auto", "docSummary": null,
                             "summaryStatus": "planned", "metaAssociateMethod": null},
                "config": {"id": "20557", "docId": "DOC_d61cdd48e2c845aabcf436bce49eba8d", "analysisType": null, "parseMethod": "0",
                           "attachId": null, "sliceMethod": 1, "sliceByParagraph": 1, "ocrType": 0, "removeToc": 1,
                           "headerHeight": null, "footerHeight": null, "associatedWithName": null,
                           "sliceIdentifier": "[\"。\",\"！\",\"!\",\"？\",\"?\",\"，\",\",\",\"：\",\":\",\".\"]",
                           "sliceMaxLength": 500, "sliceProportion": 10, "conversionFactor": null, "relateInfo": null,
                           "creator": "nrgtest", "createTime": "2025-12-01 10:55:16", "updateTime": null, "contextLength": 8000,
                           "ocrOpen": null}}, "ok": true}
        """
        api = f'api/zspt/zsgl/knowledgeBaseDocument/detail'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, docId=docId)
        return res

    def doc_page_list(self, docId, total, keyword='', current=1, size=10):
        """
        查询文档的学习结果
        :param docId:
        :param keyword:
        :param total: 80
        :param current: 1
        :param size: 10
        :return: {"msg": null, "code": 200, "data":
         {"total": 80, "current": 1, "pages": 8, "size": 10, "records": [
          {"chunk_size": 176, "chunk_position": 29, "doc_title": "ospf", "doc_available": "1", "abstract_text": "",
             "chunk_text": "ospf#什么是OSPF？#OSPF基础概念#OSPF支持的网络类型相关内容：点到点P2P类型（point-to-point） | 当链路层协议是PPP、HDLC和LAPB时，缺省情况下，OSPF认为网络类型是P2P。 在该类型的网络中，以组播形式（224.0.0.5）发送协议报文（Hello报文、DD报文、LSR报文、LSU报文、LSAck报文）。",
             "doc_id": "DOC_d61cdd48e2c845aabcf436bce49eba8d", "chunk_id": "3158d362ce6111f0ab8e02a65fdc6d6a",
             "question_text": "", "chunk_available": "1", "page_index": 1,
             "chunk_title": "#什么是OSPF？#OSPF基础概念#OSPF支持的网络类型",
             "knowledge_id": "KLB_f1b895e57a3e4851939483e11f84ee6a"},
        ]}}
        """
        api = f'api/zspt/zsgl/knowledgeBaseDocument/page'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, docId=docId, keyword=keyword, total=total,
                                current=current, size=size)
        return res

    def doc_get_chunk_all(self, docId, size=10):
        """
        获取指定doc下的所有切片
        :param docId:
        :param size: 10
        :return: 'docName', [{"chunk_size": 176, "chunk_position": 29, "doc_title": "ospf", "doc_available": "1", "abstract_text": "",
             "chunk_text": "ospf#什么是OSPF？#OSPF基础概念#OSPF支持的网络类型相关内容：点到点P2P类型（point-to-point） | 当链路层协议是PPP、HDLC和LAPB时，缺省情况下，OSPF认为网络类型是P2P。 在该类型的网络中，以组播形式（224.0.0.5）发送协议报文（Hello报文、DD报文、LSR报文、LSU报文、LSAck报文）。",
             "doc_id": "DOC_d61cdd48e2c845aabcf436bce49eba8d", "chunk_id": "3158d362ce6111f0ab8e02a65fdc6d6a",
             "question_text": "", "chunk_available": "1", "page_index": 1,
             "chunk_title": "#什么是OSPF？#OSPF基础概念#OSPF支持的网络类型",
             "knowledge_id": "KLB_f1b895e57a3e4851939483e11f84ee6a"},....]
        """
        total_size = self.doc_detail(docId)['data']['document']['sliceNum']
        doc_name = self.doc_detail(docId)['data']['document']['docName']
        page = 1
        data = []
        while page < math.ceil(total_size / size):
            data.extend(self.doc_page_list(docId, total_size, current=page, size=size)['data']['records'])
            page += 1
        return doc_name, data
