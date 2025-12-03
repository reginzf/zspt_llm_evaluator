def retrieve_format_for_label_studio(records):
    """
    传入紫鸾平台 webKnowledgeRetrieve返回的res['data']['records']
    :param records:
    :return:
    """
    res = []
    for data in records:
        # 去掉title和固定字段，剩余为text
        text_start = len(data["doc_name"] + data["chunk_title"]) + 5
        res.append({
            "text": data["chunk_text"][text_start::],
            # 自定义字段
            "size": data["chunk_size"],
            "chunk_title": data["chunk_title"],
            "score": data["score"],
            "metaData": data["metaData"],
            "fileName": data["fileName"],
        })
    return res
