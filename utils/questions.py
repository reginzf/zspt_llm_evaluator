import json
from jsonpath import jsonpath
from typing import Dict, List, Any, Optional, Tuple


def get_questions(json_data, q_type):
    """

    :param json_data:
    :param q_type:
    :return:{'type': 'factual', 'label_type': 'Choice', 'label_config': {'choice': 'multiple'},
    'questions': ['ospf中有哪些类型的报文', 'ospf中的router Id是用来做什么的']}
    """
    # 获取问题
    questions = jsonpath(json_data, f'$.datas[?(@.type=="{q_type}")')
    if questions:
        questions = questions[0]
    return questions


def find_question_info(data: Dict[str, Any], target_question: str) -> Optional[Dict[str, str]]:
    """
    查找特定问题对应的信息

    Args:
        data: JSON数据
        target_question: 要查找的问题文本

    Returns:
        包含type和label_type的字典，如果未找到则返回None
    """
    for item in data["datas"]:
        questions = item.get("questions", [])
        if target_question in questions:
            return {
                "type": item.get("type"),
                "label_type": item.get("label_type"),
                "question": target_question,
                "label_config": item.get("label_config", {})
            }
    return None


def get_question_type_and_label(question_json, question_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    获取问题的type和label_type

    Args:
        question_json: 所有问题JSON
        question_text: 问题文本

    Returns:
        (type, label_type) 元组，如果未找到则返回(None, None)
    """

    info = find_question_info(question_json, question_text)
    if info:
        return info["type"], info["label_type"]
    return None, None
