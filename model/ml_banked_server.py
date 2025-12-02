from label_studio_ml.model import LabelStudioMLBase
from flask import Flask, request, jsonify
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# 确保环境变量在导入 transformers 之前设置
import os

os.environ['HUGGINGFACE_CO_URL_HOME'] = "https://hf-mirror.com/"
os.environ['_HF_DEFAULT_ENDPOINT'] = "https://hf-mirror.com/"
_HF_DEFAULT_ENDPOINT = "https://hf-mirror.com"
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_OFFLINE'] = '0'  # 确保在线模式

from transformers import pipeline
import numpy as np

# 初始化 Flask 应用
app = Flask(__name__)


class MyModel(LabelStudioMLBase):
    def __init__(self, **kwargs):
        super(MyModel, self).__init__(**kwargs)
        # 加载 bert-base-uncased 模型
        self.model_name = "hfl/chinese-roberta-wwm-ext"
        # 使用 pipeline 方式（更简单）
        self.classifier = pipeline("text-classification", model=self.model_name)

    def predict(self, tasks, **kwargs):
        """处理预测请求"""
        predictions = []
        for task in tasks:
            # 实现预测逻辑
            result = self._predict_single_task(task)
            predictions.append(result)
        return predictions

    def _predict_single_task(self, task):
        # 单个任务预测实现
        try:
            # 获取文本数据
            text_data = task['data'].get('text', '')
            print(task)
            if not text_data:
                return {
                    'result': [],
                    'score': 0.0
                }

            # 使用 transformers pipeline 进行预测（推荐方式）
            result = self.classifier(text_data)
            predicted_label = result[0]['label']
            confidence = result[0]['score']

            print(predicted_label)
            return {
                'result': [{
                    'from_name': 'choice',  # 需要与 Label Studio 配置匹配
                    'to_name': 'text',  # 需要与 Label Studio 配置匹配
                    'type': 'choices',
                    'value': {
                        'choices': [predicted_label]
                    }
                }],
                'score': confidence
            }
        except Exception as e:
            logging.error(f"Prediction error: {str(e)}")
            return {
                'result': [],
                'score': 0.0
            }


# 创建模型实例
model = MyModel()


@app.route('/predict', methods=['POST'])
def predict():
    tasks = request.json.get('tasks')
    predictions = model.predict(tasks)
    return jsonify({'predictions': predictions})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'UP'})


@app.route('/setup', methods=['POST'])
def setup():
    """处理 Label Studio 的 setup 请求"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090,debug=True)
