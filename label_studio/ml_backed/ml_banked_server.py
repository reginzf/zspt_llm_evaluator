from label_studio_ml.model import LabelStudioMLBase
from flask import Flask, request, jsonify
import logging
import torch
from transformers import AutoTokenizer, AutoModel
import os
import numpy as np
import json
from pathlib import Path
from env_config_init import QUESTION_JSON, settings

# 初始化 Flask 应用
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MyModel(LabelStudioMLBase):
    """
    使用 bge-base-zh-v1.5 本地模型进行文本分类预测
    通过计算输入文本与标签文本的相似度来进行分类
    """

    def __init__(self, **kwargs):
        super(MyModel, self).__init__(**kwargs)

        self.model_path = settings.MODEL_PATH
        self.SIMILARITY_THRESHOLD = settings.SIMILARITY_THRESHOLD

        # 加载标签配置
        self._load_label_config()

        # 加载 tokenizer 和模型
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModel.from_pretrained(self.model_path)

        # 设置设备
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

        logger.info(f"Model loaded successfully, using device: {self.device}")
        logger.info(f"Label categories: {list(self.LABEL_CONFIG.keys())}")

        # 预计算所有标签的 embeddings
        self._precompute_label_embeddings()

    def _load_label_config(self):
        """从 JSON 文件加载标签配置"""
        config_data = QUESTION_JSON
        # 转换配置文件格式
        self.LABEL_CONFIG = {}
        for item in config_data.get('datas', []):
            category = item['type']
            questions = item['questions']

            self.LABEL_CONFIG[category] = {
                "from_name": category,
                "choices": questions
            }

        logger.info(f"Loaded {len(self.LABEL_CONFIG)} label categories from config")
        logger.debug(f"Label config: {json.dumps(self.LABEL_CONFIG, ensure_ascii=False, indent=2)}")

    def _get_embedding(self, texts):
        """
        获取文本的 embedding
        BGE 模型推荐在查询文本前添加指令前缀
        """
        if isinstance(texts, str):
            texts = [texts]

        # 对于 BGE 模型，查询时可以添加前缀（可选）
        encoded_input = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        ).to(self.device)

        with torch.no_grad():
            model_output = self.model(**encoded_input)
            # 使用 [CLS] token 的 embedding 作为句子表示
            embeddings = model_output.last_hidden_state[:, 0]

        # 归一化
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        return embeddings.cpu().numpy()

    def _precompute_label_embeddings(self):
        """预计算所有标签文本的 embeddings"""
        logger.info("Precomputing label embeddings...")

        self.label_embeddings = {}

        for category, config in self.LABEL_CONFIG.items():
            choices = config["choices"]
            embeddings = self._get_embedding(choices)
            self.label_embeddings[category] = {
                "choices": choices,
                "embeddings": embeddings
            }

        logger.info(f"Label embeddings computed for {len(self.label_embeddings)} categories")

    def _compute_similarity(self, query_embedding, label_embeddings):
        """计算查询文本与标签的余弦相似度"""
        # 由于已经归一化，直接点积即为余弦相似度
        similarities = np.dot(label_embeddings, query_embedding.T).flatten()
        return similarities

    def predict(self, tasks, **kwargs):
        """处理预测请求"""
        predictions = []
        for task in tasks:
            result = self._predict_single_task(task)
            predictions.append(result)
        return predictions

    def _predict_single_task(self, task):
        """单个任务预测实现"""
        try:
            # 获取文本数据
            text_data = task['data'].get('text', '')
            task_id = task.get('id', 'unknown')
            logger.info(f"Processing task {task_id}")
            logger.debug(f"Text preview: {text_data[:200]}...")

            if not text_data:
                logger.warning(f"Task {task_id}: Empty text data")
                return {
                    'result': [],
                    'score': 0.0
                }

            # 获取输入文本的 embedding
            query_embedding = self._get_embedding(text_data)

            results = []
            total_score = 0.0
            matched_count = 0

            # 对每个类别进行预测
            for category, config in self.LABEL_CONFIG.items():
                label_data = self.label_embeddings[category]
                choices = label_data["choices"]
                embeddings = label_data["embeddings"]

                # 计算相似度
                similarities = self._compute_similarity(query_embedding, embeddings)

                # 找出相似度最高的标签
                max_idx = np.argmax(similarities)
                max_similarity = similarities[max_idx]

                # 如果相似度超过阈值，则添加到结果中
                if max_similarity >= self.SIMILARITY_THRESHOLD:
                    matched_choice = choices[max_idx]

                    results.append({
                        'from_name': config["from_name"],
                        'to_name': 'text',
                        'type': 'choices',
                        'value': {
                            'choices': [matched_choice]
                        }
                    })

                    total_score += max_similarity
                    matched_count += 1

                    logger.info(
                        f"Task {task_id}: Matched {category} -> '{matched_choice}' (score: {max_similarity:.4f})")
                else:
                    logger.debug(
                        f"Task {task_id}: {category} max similarity {max_similarity:.4f} < threshold {self.SIMILARITY_THRESHOLD}")

            # 计算平均置信度
            avg_score = total_score / matched_count if matched_count > 0 else 0.0

            logger.info(f"Task {task_id}: {matched_count} matches, average score: {avg_score:.4f}")

            return {
                'result': results,
                'score': float(avg_score)
            }

        except Exception as e:
            logger.error(f"Prediction error for task {task.get('id', 'unknown')}: {str(e)}", exc_info=True)
            return {
                'result': [],
                'score': 0.0
            }

    def fit(self, event, data, **kwargs):
        """
        训练/微调模型（可选实现）
        当 Label Studio 中有新的标注数据时会调用此方法
        """
        logger.info("Fit method called - not implemented for embedding-based model")
        pass


# 创建模型实例
model = MyModel()


@app.route('/predict', methods=['POST'])
def predict():
    """处理预测请求"""
    try:
        tasks = request.json.get('tasks', [])
        logger.info(f"Received predict request with {len(tasks)} tasks")
        predictions = model.predict(tasks)
        logger.info(f"Predictions: {predictions}")
        return jsonify({'predictions': predictions})
    except Exception as e:
        logger.error(f"Predict endpoint error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'UP',
        'model': 'bge-base-zh-v1.5',
        'label_config_path': model.label_config_path,
        'similarity_threshold': model.SIMILARITY_THRESHOLD,
        'categories': list(model.LABEL_CONFIG.keys())
    })


@app.route('/setup', methods=['POST'])
def setup():
    """处理 Label Studio 的 setup 请求"""
    schema = request.json.get('schema', '')
    logger.info(f"Setup request received")

    # 返回模型信息
    return jsonify({
        'status': 'ok',
        'model_version': 'bge-base-zh-v1.5',
        'label_config_path': model.label_config_path,
        'labels': list(model.LABEL_CONFIG.keys()),
        'similarity_threshold': model.SIMILARITY_THRESHOLD
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """处理 Label Studio webhook 请求"""
    data = request.json
    logger.info(f"Webhook received: {data.get('action', 'unknown')}")
    return jsonify({'status': 'ok'})


@app.route('/config', methods=['GET'])
def get_config():
    """获取当前配置信息"""
    return jsonify({
        'label_config': model.LABEL_CONFIG,
        'label_config_path': model.label_config_path,
        'similarity_threshold': model.SIMILARITY_THRESHOLD,
        'model_path': model.model_path
    })


if __name__ == '__main__':
    logger.info("Starting ML Backend Server...")
    app.run(host='0.0.0.0', port=9090, debug=True)
