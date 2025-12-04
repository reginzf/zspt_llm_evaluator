from jsonpath import jsonpath


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
