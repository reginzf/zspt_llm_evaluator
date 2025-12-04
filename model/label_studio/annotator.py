from label_studio_sdk._legacy import Project
import requests


class Annotator:
    def __init__(self, project: Project):
        self.project = project
        self.url = project.url
        self.headers = project.headers

    def generate_filter_item(self, value, filter, operator, type):
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
        self.project.get_task()
        return tasks

    def create_annotation_data(self, value, from_name, to_name, type):
        # 构建标注结果
        result = []
        result.append({
            "from_name": from_name,
            "to_name": to_name,
            "type": type,
            "value": value
        })

    def create_annotation(self, task_id, annotation_data):
        """"""
        url = f"{self.url}/api/tasks/{task_id}/annotations?project={self.project.id}"
        response = requests.post(url, headers=self.headers, json=annotation_data)
        if response.status_code == 201:
            annotation_id = response.json().get('id')
            print(f"✅ 标注创建成功！标注ID: {annotation_id}")
            return {
                "success": True,
                "annotation_id": annotation_id,
                "data": response.json()
            }
        else:
            print(f"❌ 标注创建失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
