# 模板定义
LABEL_STUDIO_TEMPLATE = {
    "text": "",
    # 自定义字段
    "size": None,
    "chunk_title": "",
    "chunk_id": "",
    "score": None,
    "metaData": None,
    "fileName": "",
    "start_at": None
}


def retrieve_format_for_label_studio(records):
    """
    将召回的切片转换为label studio 的格式
    传入紫鸾平台 webKnowledgeRetrieve返回的res['data']['records']
    :param records:
    :return:
    """
    res = []
    for data in records:
        # 去掉title和固定字段，剩余为text
        item = LABEL_STUDIO_TEMPLATE.copy()
        item.update({
            "text": data["chunk_text"],
            # 自定义字段
            "size": data["chunk_size"],
            "chunk_title": data["chunk_title"],
            "chunk_id": data["chunk_id"],
            "score": data["score"],
            "metaData": data["metaData"],
            "fileName": data["fileName"],
        })
        res.append(item)
    return res


def doc_slices_format_for_label_studio(records):
    """
    将文档切片转换为label studio 的格式
    :param doc_name:
    :param records:KnowledgeBasePage.doc_get_chunk_all的返回
    :return:
    """
    res = []
    print(records)
    for data in records:
        # 去掉title和固定字段，剩余为text

        item = LABEL_STUDIO_TEMPLATE.copy()
        item.update({
            "text": data["chunk_text"],
            # 自定义字段
            "size": data["chunk_size"],
            "chunk_title": data["chunk_title"],
            "chunk_id": data["chunk_id"],
            "score": None,
            "metaData": None,
            "fileName": data["doc_title"],
        })
        res.append(item)
    return res
