import jsonpath
from label_studio_sdk._legacy import Project
import requests

VALUE_KEY_MAP = {
    "Choice": 'choices'
}

FROM_NAME_SET = {'factual', 'contextual', 'conceptual', 'reasoning'}


class Annotator:
    def __init__(self, project: Project):
        self.project = project
        self.url = project.url
        self.headers = project.headers

    def generate_filter_item(self, value, filter, type="String", operator="equal"):
        """
        生成filter结构体
        :param value: 要过滤的值
        :param filter: 过滤器 filter:tasks:data.chunk_id
        :param operator: equal
        :param type: String
        :return:
        """
        return {
            "filter": filter,
            "operator": operator,
            "value": value,
            "type": type
        }

    def get_task_by_filter(self, filter_items: list, conjunction="and", **kwargs):
        """
        获取需要标注的任务
        :param value: 比较的值，如按chunk_id比较
        :param filter_str: eg
        :param conjunction: and | or
        :param operator: equal
        :param type: String
        :return: [task_id1,task_id2...]
        """
        filters = {"conjunction": conjunction, "items": []}
        for item in filter_items:
            filters["items"].append(self.generate_filter_item(**item))
        tasks = self.project.get_tasks(filters=filters)
        return tasks

    def create_annotation_data(self, value, from_name, to_name, type, result=None):
        # 构建标注结果
        result = result if result is not None else []
        result.append({
            "from_name": from_name,
            "to_name": to_name,
            "type": type,
            "value": {
                type: [value]}
        })

    def create_annotation(self, task_id, annotation_data, http_method='POST'):
        """"""
        url = f"{self.url}/api/tasks/{task_id}/annotations?project={self.project.id}"
        if http_method == 'POST':
            response = requests.post(url, headers=self.headers, json=annotation_data)
        elif http_method == 'PATCH':
            response = requests.patch(url, headers=self.headers, json=annotation_data)
        else:
            raise ValueError("http_method参数错误,支持POST|PATCH")
        if response.status_code == 201:
            annotation_id = response.json().get('id')
            print(f"✅ 标注创建成功！标注ID: {annotation_id}")
            return {
                "success": True,
                "annotation_id": annotation_id,
                "data": response.json()
            }
        else:
            print(f"❌ 标注创建失败: {response.status_code},错误信息: {response.text}")
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }

    def task_annotate(self, task: dict, annotation_data):
        """
        对task进行标注
        :param task_id:
        :param annotation_data:
        :return:
        """
        if task["total_annotations"] != 0:
            # 获取所有的result
            results = jsonpath.jsonpath(task, "$.annotations[*].result")[0]
            results.append(annotation_data)
            return self.create_annotation(task["id"], results, http_method='PATCH')
        else:
            return self.create_annotation(task["id"], annotation_data)


if __name__ == '__main__':
    # 在project下获得对应的task
    from label_studio_sdk._legacy import Project
    from model.label_studio.label_studio_client import label_studio_client

    project = label_studio_client.get_projects(title="ospf_chunk_test")[0]
    annotator = Annotator(project)
    task_filter = annotator.generate_filter_item('5dd35eacd01f11f09ee902a65fdc6d6a', "filter:tasks:data.chunk_id")
    target_task = annotator.get_task_by_filter([task_filter])
    print(target_task)

    # 获取对应chunk_id的task
    # task = annotator.get_task_by_filter()
