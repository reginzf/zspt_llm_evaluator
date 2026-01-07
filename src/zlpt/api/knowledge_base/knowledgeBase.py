import jsonpath

from src.zlpt.api.base_client import BaseClient
import math
import os
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder

SLICEIDENTIFIER = ["。", "！", "!", "？", "?", "，", ",", "：", ":", "."]


class KnowledgeBase(BaseClient):
    def knowledge_addOrUpdate(
            self,
            knowledgeName,
            description='',
            kno_id=None,
            visibleRange=0,
            deptIdList=None,
            manageDeptIdList=None,
    ):
        """
        创建、更新，当id有值时为更新
        :param knowledgeName:
        :param description:
        :param visibleRange:
        :param deptIdList:
        :param manageDeptIdList:
        :return:{"code":200,"msg":null,"data":null,"ok":true}
        """
        if deptIdList is None:
            deptIdList = []
        if manageDeptIdList is None:
            manageDeptIdList = [""]

        api = 'api/zspt/zsgl/knowledgeBase/addOrUpdate'
        method = 'POST'
        data = {
            "knowledgeName": knowledgeName,
            "description": description,
            "visibleRange": visibleRange,
            "deptIdList": deptIdList,
            "manageDeptIdList": manageDeptIdList
        }
        if kno_id is not None:
            data["id"] = kno_id
        res = self.send_request(api, method, data)
        return res

    def knowledge_content_tree(self, knowledgeId, name=""):
        """
        查询目录结构
        :param knowledgeId:
        :param name:
        :return:     {"code": 200, "msg": null, "data": [{"id": "8050", "knowledgeId": "KLB_869cb0ded2c64362a2b5ce722d2e91cf",
                                         "contentCode": "5348b1ffa40949d3a955f8f60d64aac6",
                                         "contentName": "ospf_chunk_600", "children": [], "psort": 1, "plevel": 0,
                                         "pcontentCode": null}], "ok": true}
        """
        api = 'api/zspt/zsgl/knowledgeBaseContent/tree'
        method = 'GET'
        data = {}
        res = self.send_request(api, method, data, knowledgeId=knowledgeId, name=name)
        return res

    def doc_addOrUpdate(
            self,
            knowledgeId,
            contentCode,
            tmpFolderName: list,
            chunk_size=500,
            chunk_overlap=10,
            associatedWithName="1",
            sliceIdentifier=None,
            sliceMethod='1'
    ):
        """
        上传文件
        :param knowledgeId:
        :param contentCode:
        :param tmpFolderName: 通过doc_upload_attachment 的id获取
        :param chunk_size:
        :param chunk_overlap:
        :param associatedWithName:
        :param sliceIdentifier:
        :param sliceMethod: # 0 默认切片 1 自定义切片 2 放入一整个切片
        :return:{"code":200,"msg":null,"data":null,"ok":true}
        """
        api = 'api/zspt/zsgl/knowledgeBaseDocument/addOrUpdate'
        method = 'POST'
        sliceIdentifier = sliceIdentifier or SLICEIDENTIFIER
        data = {
            "knowledgeId": knowledgeId,
            "contentCode": contentCode,
            "webUrlDtos": [],
            "importFileType": 0,
            "tmpFolderName": tmpFolderName,
            "analysisType": "0",
            "parseMethod": "0",
            "headerHeight": 40,
            "footerHeight": 40,
            "sliceMethod": sliceMethod,
            "sliceByParagraph": 1,
            "sliceIdentifier": sliceIdentifier,
            "sliceMaxLength": chunk_size,
            "sliceProportion": chunk_overlap,
            "associatedWithName": associatedWithName,
            "ocrOpen": 1,
            "ocrType": 0,
            "removeToc": 1,
            "contextLength": 8000,
            "metaData": "{\"tags\":[]}"
        }
        res = self.send_request(api, method, data)
        return res

    def upload_attachment(self, file_path, content_code, import_file_type="0"):
        """
        上传附件文件

        该接口用于上传附件到知识库系统，支持单个文件上传。

        :param file_path: 要上传的文件路径（字符串）
        :param content_code: 内容编码，用于关联知识内容（字符串）
        :param import_file_type: 导入文件类型，默认为0（整数，可选）
        :return: {"code":200,"msg":null,"data":"c3778a214de84ceb8742705c691afaaf","ok":true}
        """
        url = self.base_url + "/api/zspt/zsgl/file/attach/uploadAttachment"
        m = MultipartEncoder(
            fields={
                'files': (os.path.basename(file_path), open(file_path, 'rb'), "application/plain"),
                'importFileType': import_file_type,
                'contentCode': content_code
            }
        )
        res = self.sess.post(url, data=m, headers={'Content-Type': m.content_type}, verify=False)
        res = json.loads(res.content.decode("utf-8"))
        return res

    def knowledge_delete(self, knowledgeId):
        """
        删除数据库
        :param knowledgeId:
        :return: {"code":200,"msg":null,"data":null,"ok":true}
        """
        api = f'api/zspt/zsgl/knowledgeBase/delete'
        method = 'DELETE'
        data = {}
        res = self.send_request(api, method, data, knowledgeId=knowledgeId)
        return res

    def knowledge_list(self, knowledgeBaseName, visibleRange=None):
        """
        查询知识库列表
        :param knowledgeBaseName:
        :param visibleRange: 1 部分可见
        :return: {"code": 200, "msg": null, "data": [
        {"id": 68, "knowledgeName": "ospf_chunk_600", "knowledgeId": "KLB_869cb0ded2c64362a2b5ce722d2e91cf",
         "description": null, "creatorUserName": "nrgtest", "creatorRealName": null,
         "createTime": "2025-12-03 15:47:31", "updateTime": "2025-12-03 16:09:25", "docCount": 1, "visibleRange": 0,
         "deptIdList": [], "manageDeptIdList": [""]},
       ], "ok": true}
        """
        api = f'api/zspt/zsgl/knowledgeBase/knowledgeList'
        method = 'GET'
        data = {}
        if visibleRange:
            res = self.send_request(api, method, data, knowledgeBaseName=knowledgeBaseName, visibleRange=visibleRange)
        else:
            res = self.send_request(api, method, data, knowledgeBaseName=knowledgeBaseName)
        return res

    def knowledge_doc_list(self, knowledgeId, docName='', docSource="0,1,2", current=1, size=25):
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
        method = 'GET'
        data = {}
        res = self.send_request(
            api,
            method,
            data,
            knowledgeId=knowledgeId,
            docName=docName,
            docSource=docSource,
            current=current,
            size=size
        )
        return res

    def knowledge_content_add_or_update(self, knowledgeId, contentName, parentContentCode):
        """
        创建目录
        :param knowledgeId:知识库id
        :param contentName:目录名称
        :param parentContentCode: 上级目录id，如果不带则在根目录更新
        :return:{"code":200,"msg":null,"data":null,"ok":true}
        """
        api = f'api/zspt/zsgl/knowledgeBaseContent/addOrUpdate'
        method = 'POST'
        data = {"contentName": contentName, "knowledgeId": knowledgeId}
        if parentContentCode:
            data.update({"parentContentCode": parentContentCode})
        res = self.send_request(api, method, data)
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
        method = 'GET'
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
        method = 'GET'
        data = {}
        res = self.send_request(
            api,
            method,
            data,
            docId=docId,
            keyword=keyword,
            total=total,
            current=current,
            size=size
        )
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
        res = self.doc_detail(docId)
        total_size = res['data']['document']['sliceNum']
        doc_name = res['data']['document']['docName']
        page = 1
        data = []
        while page < math.ceil(total_size / size) + 1:
            data.extend(self.doc_page_list(docId, total_size, current=page, size=size)['data']['records'])
            page += 1
        return doc_name, data


if __name__ == '__main__':
    from env_config_init import settings
    from zlpt.login import LoginManager

    login_manager = LoginManager(settings.ZLPT_BASE_URL)
    login_manager.login(settings.USERNAME, settings.PASSWORD, settings.DOMAIN)
    login_manager.get_auth_key()
    knowledge_base = KnowledgeBase(login_manager)
    kno_id = "KLB_869cb0ded2c64362a2b5ce722d2e91cf"
    target_path = r'/tests/ospf/context/OSPFv2.txt'
    cont_id = jsonpath.jsonpath(knowledge_base.knowledge_content_tree(kno_id),
                                '$.data[0].contentCode')[0]
    file_id = knowledge_base.upload_attachment(target_path, cont_id)['data']
    print(cont_id, file_id)
    print(knowledge_base.doc_addOrUpdate(kno_id, cont_id, [file_id]))
