import jsonpath
from label_studio_sdk._legacy import Project
import requests
from typing import List, Dict, Any, Optional, Union
from enum import Enum

__all__ = ["AnnotationOperation", "AnnotationGenerator", "AnnotateToAdd", "AnnotateToCreate", "Annotator"]
VALUE_KEY_MAP = {
    "choices": 'choices',
    "labels": 'labels',
    "rectanglelabels": 'rectanglelabels',
    "number": 'number',
    "textarea": 'text',
    "rating": 'rating'
}

FROM_NAME_SET = {'factual', 'contextual', 'conceptual', 'reasoning'}


class AnnotationOperation(Enum):
    """标注操作类型"""
    ADD = "add"  # 向现有标注添加内容
    CREATE = "create"  # 创建新标注
    DELETE = "delete"  # 删除标注内容


class AnnotationGenerator:
    """标注数据生成器"""

    @staticmethod
    def generate_choice_annotation(from_name: str, to_name: str = 'text',
                                   choices: List[str] = None, type: str = "choices") -> Dict:
        """
        生成选择题标注数据

        Args:
            from_name: 标签名称
            to_name: 目标名称
            choices: 选择的选项列表/question
            type: 标注类型

        Returns:
            标注数据字典
        """
        return {
            "from_name": from_name,
            "to_name": to_name,
            "type": type,
            "value": {
                VALUE_KEY_MAP.get(type, type): choices
            }
        }

    @staticmethod
    def generate_text_annotation(from_name: str, to_name: str,
                                 text: str) -> Dict:
        """
        生成文本标注数据

        Args:
            from_name: 标签名称
            to_name: 目标名称
            text: 文本内容

        Returns:
            标注数据字典
        """
        return {
            "from_name": from_name,
            "to_name": to_name,
            "type": "textarea",
            "value": {
                "text": [text]
            }
        }

    @staticmethod
    def generate_number_annotation(from_name: str, to_name: str,
                                   number: Union[int, float]) -> Dict:
        """
        生成数字标注数据

        Args:
            from_name: 标签名称
            to_name: 目标名称
            number: 数字值

        Returns:
            标注数据字典
        """
        return {
            "from_name": from_name,
            "to_name": to_name,
            "type": "number",
            "value": {
                "number": number
            }
        }

    @staticmethod
    def generate_rating_annotation(from_name: str, to_name: str,
                                   rating: int, max_rating: int = 5) -> Dict:
        """
        生成评分标注数据

        Args:
            from_name: 标签名称
            to_name: 目标名称
            rating: 评分值
            max_rating: 最大评分

        Returns:
            标注数据字典
        """
        return {
            "from_name": from_name,
            "to_name": to_name,
            "type": "rating",
            "value": {
                "rating": rating
            }
        }

    @staticmethod
    def generate_labels_annotation(from_name: str, to_name: str,
                                   labels: List[str],
                                   start: Optional[int] = None,
                                   end: Optional[int] = None,
                                   text: Optional[str] = None) -> Dict:
        """
        生成标签标注数据（用于NER等）

        Args:
            from_name: 标签名称
            to_name: 目标名称
            labels: 标签列表
            start: 起始位置
            end: 结束位置
            text: 文本内容

        Returns:
            标注数据字典
        """
        value = {"labels": labels}
        if start is not None:
            value["start"] = start
        if end is not None:
            value["end"] = end
        if text is not None:
            value["text"] = text

        return {
            "from_name": from_name,
            "to_name": to_name,
            "type": "labels",
            "value": value
        }


class AnnotateToAdd:
    """向现有标注添加内容的配置"""

    def __init__(self, from_name: str, to_name: str,
                 value: Any, type: str = "choices"):
        """
        初始化添加标注配置

        Args:
            from_name: 标签名称
            to_name: 目标名称
            value: 要添加的值
            type: 标注类型
        """
        self.from_name = from_name
        self.to_name = to_name
        self.value = value
        self.type = type

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "operation": AnnotationOperation.ADD.value,
            "from_name": self.from_name,
            "to_name": self.to_name,
            "type": self.type,
            "value": self.value
        }


class AnnotateToCreate:
    """创建新标注的配置"""

    def __init__(self, annotation_data: List[Dict],
                 lead_time: float = 30.0,
                 ground_truth: bool = False,
                 created_by: str = "auto_annotator",
                 merge_existing: bool = True):
        """
        初始化创建标注配置

        Args:
            annotation_data: 标注数据列表
            lead_time: 标注耗时（秒）
            ground_truth: 是否为基准标注
            created_by: 创建者
            merge_existing: 是否合并到现有标注（如果from_name已存在）
        """
        self.annotation_data = annotation_data
        self.lead_time = lead_time
        self.ground_truth = ground_truth
        self.created_by = created_by
        self.merge_existing = merge_existing

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "operation": AnnotationOperation.CREATE.value,
            "annotation_data": self.annotation_data,
            "lead_time": self.lead_time,
            "ground_truth": self.ground_truth,
            "created_by": self.created_by,
            "merge_existing": self.merge_existing
        }


class AnnotateToDelete:
    """删除标注内容的配置"""

    def __init__(self, annotation_id: Optional[int] = None,
                 from_name: Optional[str] = None,
                 condition: Optional[Dict] = None):
        """
        初始化删除标注配置

        Args:
            annotation_id: 要删除的标注ID（如果指定，则删除整个标注）
            from_name: 要删除的标注项名称（如果指定，则删除特定项）
            condition: 删除条件，如 {"type": "choices", "value": "特定值"}
        """
        self.annotation_id = annotation_id
        self.from_name = from_name
        self.condition = condition

        if annotation_id is None and from_name is None:
            raise ValueError("必须指定annotation_id或from_name")

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        result = {
            "operation": AnnotationOperation.DELETE.value
        }
        if self.annotation_id:
            result["annotation_id"] = self.annotation_id
        if self.from_name:
            result["from_name"] = self.from_name
        if self.condition:
            result["condition"] = self.condition
        return result


class Annotator:
    def __init__(self, project: Project):
        self.project = project
        self.url = project.url
        print(f"Label Studio URL: {self.url}")
        self.headers = project.headers
        self.generator = AnnotationGenerator()

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
        :param filter_items: 过滤器项列表
        :param conjunction: and | or
        :return: 任务列表
        """
        filters = {"conjunction": conjunction, "items": []}
        for item in filter_items:
            filters["items"].append(self.generate_filter_item(**item))
        tasks = self.project.get_tasks(filters=filters)
        return tasks

    def create_annotation_data(self, value, from_name, to_name, type, result=None):
        """
        创建标注数据

        Args:
            value: 标注值
            from_name: 标签名称
            to_name: 目标名称
            type: 标注类型
            result: 现有结果列表

        Returns:
            更新后的结果列表
        """
        if result is None:
            result = []

        # 根据类型确定值键名
        value_key = VALUE_KEY_MAP.get(type, type)

        # 处理不同类型的值
        if isinstance(value, list):
            value_data = value
        else:
            value_data = [value]

        result.append({
            "from_name": from_name,
            "to_name": to_name,
            "type": type,
            "value": {
                value_key: value_data
            }
        })
        return result

    def create_annotation(self, task_id, annotation_data, http_method='POST',
                          lead_time=30.0, ground_truth=False, created_by="auto_annotator",
                          prediction=False):
        """
        创建或更新标注/预测

        Args:
            task_id: 任务ID
            annotation_data: 标注数据
            http_method: HTTP方法
            lead_time: 标注耗时
            ground_truth: 是否为基准标注
            created_by: 创建者
            prediction: 是否为预测（True则创建预测，False则创建标注）

        Returns:
            操作结果
        """
        if prediction:
            url = f"{self.url}/api/predictions/"
        else:
            url = f"{self.url}/api/tasks/{task_id}/annotations?project={self.project.id}"

        # 构建完整的标注数据
        ann_data = {
            "result": annotation_data,
            "lead_time": lead_time,
            "was_cancelled": False,
            "ground_truth": ground_truth,
            "created_by": created_by
        }

        if prediction:
            # 对于预测，需要添加task和project信息
            ann_data["task"] = task_id
            ann_data["project"] = self.project.id

        if http_method == 'POST':
            response = requests.post(url, headers=self.headers, json=ann_data)
        elif http_method == 'PATCH':
            if prediction:
                # 对于预测的PATCH请求，需要先获取现有预测ID
                existing_predictions = self.get_task_predictions(task_id)
                if existing_predictions:
                    # 更新第一个预测
                    prediction_id = existing_predictions[0].get('id')
                    patch_url = f"{self.url}/api/predictions/{prediction_id}"
                    response = requests.patch(patch_url, headers=self.headers, json=ann_data)
                else:
                    # 如果没有现有预测，则创建新预测
                    response = requests.post(url, headers=self.headers, json=ann_data)
            else:
                # 对于标注的PATCH请求，需要先获取现有标注ID
                existing_annotations = self.get_task_annotations(task_id)
                if existing_annotations:
                    # 更新第一个标注
                    annotation_id = existing_annotations[0].get('id')
                    patch_url = f"{self.url}/api/annotations/{annotation_id}/"
                    response = requests.patch(patch_url, headers=self.headers, json=ann_data)
                else:
                    # 如果没有现有标注，则创建新标注
                    response = requests.post(url, headers=self.headers, json=ann_data)
        else:
            raise ValueError("http_method参数错误,支持POST|PATCH")

        if response.status_code in [200, 201]:
            result_id = response.json().get('id')
            result_type = "预测" if prediction else "标注"
            print(f"✅ {result_type}操作成功！ID: {result_id}")
            return {
                "success": True,
                "id": result_id,
                "type": "prediction" if prediction else "annotation",
                "data": response.json()
            }
        else:
            result_type = "预测" if prediction else "标注"
            print(f"❌ {result_type}操作失败: {response.status_code},错误信息: {response.text}")
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }

    def get_task_annotations(self, task_id: int) -> List[Dict]:
        """
        获取任务的所有标注

        Args:
            task_id: 任务ID

        Returns:
            标注列表
        """
        url = f"{self.url}/api/tasks/{task_id}/annotations/"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 获取标注失败: {response.status_code}")
            return []

    def get_task_predictions(self, task_id: int) -> List[Dict]:
        """
               获取任务的所有预测

               Args:
                   task_id: 任务ID

               Returns:
                   预测列表
               """
        url = f"{self.url}/api/predictions/"
        j_data = {"project": self.project.id, "task": task_id}
        response = requests.get(url, headers=self.headers, json=j_data)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 获取预测失败: {response.status_code}")
            return []

    def task_annotate_add(self, task: dict, annotate_to_add: AnnotateToAdd) -> Dict:
        """
        向现有标注添加内容

        Args:
            task: 任务信息（从get_task_by_filter获取）
            annotate_to_add: 要添加的标注配置

        Returns:
            操作结果
        """
        task_id = task.get("id")
        if not task_id:
            return {
                "success": False,
                "error": "任务ID不存在"
            }

        # 获取现有标注
        existing_annotations = self.get_task_annotations(task_id)
        if not existing_annotations:
            return {
                "success": False,
                "error": "任务没有现有标注，请使用task_annotate_create"
            }

        # 获取第一个标注（假设只有一个标注）
        annotation = existing_annotations[0]
        annotation_id = annotation.get('id')
        current_results = annotation.get('result', [])

        # 查找是否已存在相同from_name的标注项
        existing_item_index = -1
        for i, item in enumerate(current_results):
            if item.get('from_name') == annotate_to_add.from_name:
                existing_item_index = i
                break

        # 准备要添加的数据
        add_data = self.generator.generate_choice_annotation(
            from_name=annotate_to_add.from_name,
            to_name=annotate_to_add.to_name,
            choices=annotate_to_add.value if isinstance(annotate_to_add.value, list) else [annotate_to_add.value],
            type=annotate_to_add.type
        )

        if existing_item_index >= 0:
            # 合并现有值
            existing_item = current_results[existing_item_index]
            existing_value = existing_item['value'].get(VALUE_KEY_MAP.get(annotate_to_add.type, annotate_to_add.type),
                                                        [])
            new_value = list(
                set(existing_value + add_data['value'][VALUE_KEY_MAP.get(annotate_to_add.type, annotate_to_add.type)]))
            current_results[existing_item_index]['value'][
                VALUE_KEY_MAP.get(annotate_to_add.type, annotate_to_add.type)] = new_value
        else:
            # 添加新项
            current_results.append(add_data)

        # 更新标注
        url = f"{self.url}/api/annotations/{annotation_id}/"
        update_data = {
            "result": current_results,
            "updated_at": "auto"
        }

        response = requests.patch(url, headers=self.headers, json=update_data)

        if response.status_code == 200:
            return {
                "success": True,
                "annotation_id": annotation_id,
                "message": "标注添加成功"
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }

    def task_annotate_create(self, task: dict, annotate_to_create: AnnotateToCreate, prediction=False) -> Dict:
        """
        创建新标注

        Args:
            task: 任务信息
            annotate_to_create: 要创建的标注配置
            prediction: 是否为预测（True则保存到predictions，False则保存到annotations）

        Returns:
            操作结果
        """
        task_id = task.get("id")
        if not task_id:
            return {
                "success": False,
                "error": "任务ID不存在"
            }

        # 获取现有标注
        if prediction:
            existing_annotations = self.get_task_predictions(task_id)
        else:
            existing_annotations = self.get_task_annotations(task_id)

        if existing_annotations:
            # 有现有标注，检查是否需要合并
            annotation = existing_annotations[0]
            annotation_id = annotation.get('id')
            current_results = annotation.get('result', [])

            # 处理要创建的新标注数据
            new_results = annotate_to_create.annotation_data
            updated_results = current_results.copy()
            merged_items = []

            for new_item in new_results:
                new_from_name = new_item.get('from_name')
                new_type = new_item.get('type')
                new_value = new_item.get('value', {})

                # 查找是否已存在相同from_name的标注项
                existing_item_index = -1
                for i, item in enumerate(updated_results):
                    if item.get('from_name') == new_from_name:
                        existing_item_index = i
                        break

                if existing_item_index >= 0:
                    # 合并现有值
                    existing_item = updated_results[existing_item_index]
                    existing_type = existing_item.get('type')

                    # 检查类型是否一致
                    if existing_type != new_type:
                        return {
                            "success": False,
                            "error": f"类型不匹配: 现有类型为{existing_type}, 新类型为{new_type}"
                        }

                    # 获取值键名
                    value_key = VALUE_KEY_MAP.get(new_type, new_type)

                    # 获取现有值和新值
                    existing_values = existing_item['value'].get(value_key, [])
                    new_values = new_value.get(value_key, [])

                    if not isinstance(existing_values, list):
                        existing_values = [existing_values]
                    if not isinstance(new_values, list):
                        new_values = [new_values]

                    # 合并值（去重）
                    merged_values = list(set(existing_values + new_values))

                    # 更新现有项
                    updated_results[existing_item_index]['value'][value_key] = merged_values
                    merged_items.append(new_from_name)

                else:
                    # 添加新项
                    updated_results.append(new_item)

            # 使用PATCH更新现有标注
            if prediction:
                url = f"{self.url}/api/predictions/{annotation_id}"
                update_data = {
                    "task": task_id,
                    "result": updated_results
                }
                response = requests.patch(url, headers=self.headers, json=update_data)

            else:
                url = f"{self.url}/api/annotations/{annotation_id}/"
                update_data = {
                    "result": updated_results,
                    "lead_time": annotate_to_create.lead_time,
                    "ground_truth": annotate_to_create.ground_truth,
                    "updated_at": "auto"
                }

                response = requests.patch(url, headers=self.headers, json=update_data)

            if response.status_code == 200:
                message = "成功添加新标注项到现有标注"
                if merged_items:
                    message = f"成功合并标注项: {', '.join(merged_items)}"

                return {
                    "success": True,
                    "annotation_id": annotation_id,
                    "merged_items": merged_items,
                    "message": message
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }

        else:
            # 没有现有标注，创建新标注
            return self.create_annotation(
                task_id=task_id,
                annotation_data=annotate_to_create.annotation_data,
                http_method='POST',
                lead_time=annotate_to_create.lead_time,
                ground_truth=annotate_to_create.ground_truth,
                created_by=annotate_to_create.created_by,
                prediction=prediction
            )

    def task_prediction_create(self, task: dict, annotate_to_create: AnnotateToCreate) -> Dict:
        """
        创建新预测

        Args:
            task: 任务信息
            annotate_to_create: 要创建的预测配置

        Returns:
            操作结果
        """
        # 调用task_annotate_create，设置prediction=True
        return self.task_annotate_create(task, annotate_to_create, prediction=True)

    def task_annotate_delete(self, task: dict, annotate_to_delete: AnnotateToDelete) -> Dict:
        """
        删除标注内容

        Args:
            task: 任务信息
            annotate_to_delete: 要删除的标注配置

        Returns:
            操作结果
        """
        task_id = task.get("id")
        if not task_id:
            return {
                "success": False,
                "error": "任务ID不存在"
            }

        # 情况1：删除整个标注
        if annotate_to_delete.annotation_id:
            url = f"{self.url}/api/annotations/{annotate_to_delete.annotation_id}/"
            response = requests.delete(url, headers=self.headers)

            if response.status_code == 204:
                return {
                    "success": True,
                    "message": f"标注 {annotate_to_delete.annotation_id} 删除成功"
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }

        # 情况2：删除标注中的特定项
        existing_annotations = self.get_task_annotations(task_id)
        if not existing_annotations:
            return {
                "success": False,
                "error": "任务没有现有标注"
            }

        annotation = existing_annotations[0]
        annotation_id = annotation.get('id')
        current_results = annotation.get('result', [])

        # 过滤要删除的项
        filtered_results = []
        deleted_count = 0

        for item in current_results:
            should_delete = False

            # 检查是否匹配删除条件
            if item.get('from_name') == annotate_to_delete.from_name:
                if annotate_to_delete.condition:
                    # 检查额外条件
                    condition_met = True
                    for key, value in annotate_to_delete.condition.items():
                        if key == 'type' and item.get('type') != value:
                            condition_met = False
                            break
                        elif key == 'value':
                            item_value = item.get('value', {})
                            for val_key, val_list in item_value.items():
                                if value in val_list:
                                    condition_met = True
                                    break
                            else:
                                condition_met = False

                    if condition_met:
                        should_delete = True
                else:
                    should_delete = True

            if not should_delete:
                filtered_results.append(item)
            else:
                deleted_count += 1

        if deleted_count == 0:
            return {
                "success": False,
                "error": "未找到匹配的标注项"
            }

        # 更新标注
        url = f"{self.url}/api/annotations/{annotation_id}/"
        update_data = {
            "result": filtered_results,
            "updated_at": "auto"
        }

        response = requests.patch(url, headers=self.headers, json=update_data)

        if response.status_code == 200:
            return {
                "success": True,
                "annotation_id": annotation_id,
                "deleted_count": deleted_count,
                "message": f"成功删除 {deleted_count} 个标注项"
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }

    def task_annotate(self, task: dict, annotation_data, prediction=False):
        """
        对task进行标注（兼容旧版本）
        :param task: 任务信息
        :param annotation_data: 标注数据
        :param prediction: 是否为预测
        :return:
        """
        task_id = task.get("id")
        if task_id is None:
            raise ValueError("Task must contain 'id' key")
        # 根据是否为预测模式确定计数键名和JSON路径表达式
        count_key = "total_predictions" if prediction else "total_annotations"
        jsonpath_expr = "$.predictions[*].result" if prediction else "$.annotations[*].result"

        data_count = task.get(count_key, 0)
        if data_count != 0:
            # 获取所有的result
            results = jsonpath.jsonpath(task, jsonpath_expr)
            if results and len(results) > 0 and isinstance(results[0], list):
                results = results[0]
                results.append(annotation_data)
                return self.create_annotation(task_id, results, http_method='PATCH', prediction=prediction)
        return self.create_annotation(task["id"], annotation_data, prediction=prediction)


# 使用示例
def example_usage():
    """使用示例"""
    from label_studio_sdk._legacy import Project

    # 假设已经获取到project
    project = Project(...)  # 您的项目实例
    annotator = Annotator(project)

    # 1. 获取任务
    task_filter = annotator.generate_filter_item(
        value='5dd35eacd01f11f09ee902a65fdc6d6a',
        filter="filter:tasks:data.chunk_id"
    )
    tasks = annotator.get_task_by_filter([task_filter])

    if not tasks:
        print("未找到任务")
        return

    task = tasks[0]

    # 2. 创建标注配置
    # 示例1：创建新标注
    annotation_data = [
        annotator.generator.generate_choice_annotation(
            from_name="factual",
            to_name="text",
            choices=["ospf中有哪些类型的报文"]
        ),
        annotator.generator.generate_number_annotation(
            from_name="score",
            to_name="text",
            number=4
        )
    ]

    annotate_to_create = AnnotateToCreate(
        annotation_data=annotation_data,
        lead_time=45.5,
        ground_truth=True,
        created_by="expert_annotator"
    )

    # 创建标注
    result1 = annotator.task_annotate_create(task, annotate_to_create)
    print(f"创建标注结果: {result1}")

    # 示例2：向现有标注添加内容
    annotate_to_add = AnnotateToAdd(
        from_name="factual",
        to_name="text",
        value="ospf中的router Id是用来做什么的",
        type="choices"
    )

    result2 = annotator.task_annotate_add(task, annotate_to_add)
    print(f"添加标注结果: {result2}")

    # 示例3：删除标注内容
    annotate_to_delete = AnnotateToDelete(
        from_name="factual",
        condition={"value": "ospf中有哪些类型的报文"}
    )

    result3 = annotator.task_annotate_delete(task, annotate_to_delete)
    print(f"删除标注结果: {result3}")


def quick_example():
    """快速使用示例"""
    from label_studio_sdk._legacy import Project

    project = Project(...)  # 您的项目实例
    annotator = Annotator(project)

    # 获取任务
    task_filter = annotator.generate_filter_item(
        value='your_chunk_id',
        filter="filter:tasks:data.chunk_id"
    )
    tasks = annotator.get_task_by_filter([task_filter])

    if tasks:
        task = tasks[0]

        # 使用生成器创建标注数据
        generator = AnnotationGenerator()

        # 创建选择题标注
        choice_annotation = generator.generate_choice_annotation(
            from_name="factual",
            to_name="text",
            choices=["ospf中有哪些类型的报文", "ospf中的router Id是用来做什么的"]
        )

        # 创建评分标注
        rating_annotation = generator.generate_number_annotation(
            from_name="score",
            to_name="text",
            number=5
        )

        # 创建标注
        annotate_to_create = AnnotateToCreate(
            annotation_data=[choice_annotation, rating_annotation],
            lead_time=30.0,
            created_by="auto_system"
        )

        result = annotator.task_annotate_create(task, annotate_to_create)
        print(f"标注结果: {result}")


def example_merge_annotation():
    """合并标注示例"""
    from label_studio_sdk._legacy import Project

    project = Project(...)  # 您的项目实例
    annotator = Annotator(project)

    # 获取任务
    task_filter = annotator.generate_filter_item(
        value='chunk_id_value',
        filter="filter:tasks:data.chunk_id"
    )
    tasks = annotator.get_task_by_filter([task_filter])

    if not tasks:
        print("未找到任务")
        return

    task = tasks[0]

    # 假设任务已有标注，包含from_name="factual"
    # 现在要添加新的值到factual中

    generator = AnnotationGenerator()

    # 创建要添加的标注数据
    annotation_data = [
        generator.generate_choice_annotation(
            from_name="factual",  # 这个from_name已存在
            to_name="text",
            choices=["新增的选项1", "新增的选项2"]  # 这些值将被合并到现有值中
        ),
        generator.generate_choice_annotation(
            from_name="contextual",  # 这个from_name不存在
            to_name="text",
            choices=["新的标注项"]
        )
    ]

    annotate_to_create = AnnotateToCreate(
        annotation_data=annotation_data,
        lead_time=35.0,
        merge_existing=True  # 启用合并功能
    )

    result = annotator.task_annotate_create(task, annotate_to_create)
    print(f"合并标注结果: {result}")

    # 如果merge_existing=False，则会创建新标注
    annotate_to_create_no_merge = AnnotateToCreate(
        annotation_data=annotation_data,
        lead_time=35.0,
        merge_existing=False  # 不合并，创建新标注
    )

    result2 = annotator.task_annotate_create(task, annotate_to_create_no_merge)
    print(f"不合并创建结果: {result2}")


if __name__ == '__main__':
    # 在project下获得对应的task
    from label_studio_sdk._legacy import Project
    from label_studio_api.label_studio_client import label_studio_client

    try:
        project = label_studio_client.get_projects(title="ospf_chunk_test")[0]
        annotator = Annotator(project)

        # 获取对应chunk_id的task
        task_filter = annotator.generate_filter_item(
            '5dd35eacd01f11f09ee902a65fdc6d6a',
            "filter:tasks:data.chunk_id"
        )
        target_task = annotator.get_task_by_filter([task_filter])[0]

        # 使用新方法进行标注
        generator = AnnotationGenerator()

        # 创建标注数据
        annotation_data = [
            generator.generate_choice_annotation(
                from_name="factual",
                to_name="text",
                choices=["ospf中有哪些类型的报文"]
            )
        ]

        # 创建标注配置
        annotate_to_create = AnnotateToCreate(
            annotation_data=annotation_data,
            lead_time=25.5,
            ground_truth=True,
            created_by="manual"
        )

        # 执行标注
        result = annotator.task_annotate_create(target_task, annotate_to_create)
        print(f"标注结果: {result}")

    except Exception as e:
        print(f"执行出错: {str(e)}")
