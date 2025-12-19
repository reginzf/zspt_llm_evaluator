"""
Label Studio 预测创建器
功能：
1. 传入：label studio task的详细信息json格式，label studio的project实例
2. 通过MyModel实例，调用predict或者_predict_single_task 预测标签
3. 通过label studio sdk或者api的方式访问label studio，在对应任务下创建预测
"""

from typing import Dict, List, Any, Optional
from label_studio_sdk import Client
from label_studio_sdk._legacy import Project
from utils.logger import logger
# 导入MyModel
from label_studio_api.ml_backed.ml_banked_server import model


class LabelStudioPredictionCreator:
    """
    Label Studio 预测创建器
    用于将MyModel的预测结果上传到Label Studio
    """

    def __init__(self, label_studio_client: Client):
        """
        初始化预测创建器

        Args:
            label_studio_client: Label Studio SDK客户端实例
            model: MyModel实例，如果为None则创建新实例
        """
        self.client = label_studio_client
        self.model = model

        logger.info("LabelStudioPredictionCreator initialized")

    def create_prediction_for_task(
            self,
            task_data: Dict[str, Any],
            project: Project,
            task_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        为单个任务创建预测

        Args:
            task_data: Label Studio任务数据（JSON格式）
            project: Label Studio项目实例
            task_id: 任务ID，如果为None则从task_data中获取

        Returns:
            创建的预测信息
        """
        try:
            # 获取任务ID
            if task_id is None:
                task_id = task_data.get('id')
                if task_id is None:
                    raise ValueError("Task ID not found in task_data")

            logger.info(f"Creating prediction for task {task_id}")

            # 1. 使用MyModel进行预测
            prediction_result = self._predict_with_model(task_data)
            if len(prediction_result['result']) < 1:
                return {}
            # 2. 创建Label Studio预测
            prediction = self._create_label_studio_prediction(
                task_id=task_id,
                project=project,
                prediction_result=prediction_result
            )

            logger.info(f"Prediction created successfully for task {task_id}")
            return prediction

        except Exception as e:
            logger.error(f"Failed to create prediction for task {task_id}: {str(e)}")
            raise

    def create_predictions_for_tasks(
            self,
            tasks_data: List[Dict[str, Any]],
            project: Project
    ) -> List[Dict[str, Any]]:
        """
        为多个任务批量创建预测

        Args:
            tasks_data: Label Studio任务数据列表（JSON格式）
            project: Label Studio项目实例

        Returns:
            创建的预测信息列表
        """
        predictions = []

        for task_data in tasks_data:
            try:
                task_id = task_data.get('id')
                if task_id is None:
                    logger.warning("Skipping task without ID")
                    continue

                prediction = self.create_prediction_for_task(
                    task_data=task_data,
                    project=project,
                    task_id=task_id
                )
                predictions.append(prediction)

            except Exception as e:
                logger.error(f"Failed to create prediction for task: {str(e)}")
                continue

        logger.info(f"Created {len(predictions)} predictions out of {len(tasks_data)} tasks")
        return predictions

    def _predict_with_model(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用MyModel进行预测

        Args:
            task_data: Label Studio任务数据

        Returns:
            预测结果
        """
        # 将单个任务包装成列表，因为MyModel.predict期望任务列表
        tasks = [task_data]

        # 调用MyModel的predict方法
        predictions = self.model.predict(tasks)

        if not predictions:
            raise ValueError("No predictions returned from model")

        # 返回第一个任务的预测结果
        return predictions[0]

    def _create_label_studio_prediction(
            self,
            task_id: int,
            project: Project,
            prediction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        通过Label Studio SDK创建预测

        Args:
            task_id: 任务ID
            project: Label Studio项目实例
            prediction_result: MyModel返回的预测结果

        Returns:
            Label Studio创建的预测信息
        """
        # 准备预测数据
        prediction_data = {
            "task_id": task_id,
            "result": prediction_result.get('result', []),
            "score": prediction_result.get('score', 0.0),
            "model_version": "bge-base-zh-v1.5"
        }

        try:
            prediction = project.create_prediction(**prediction_data)
            return prediction
        except AttributeError:
            logger.info(f"{task_id}创建预测失败")


def main():
    from src.lzpt_ls_operate import login_label_studio

    project_name = 'OSPFv2_600_0'
    client = login_label_studio()
    project: Project = client.get_projects(title=project_name)[0]
    prediction_c = LabelStudioPredictionCreator(client)
    task_data = project.get_task(164)
    print(task_data)
    res = prediction_c.create_prediction_for_task(task_data, project)
    print(res)


if __name__ == "__main__":
    main()
