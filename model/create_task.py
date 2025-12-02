def create_task_with_custom_fields_sdk(text, score, start, end, metadata, title) -> dict:
    """
    单个任务的template
    :param text: 标注正文
    :param score: 匹配度  0~1
    :param start: 在整个文档中开始的位置
    :param end: 在整个文档中结束的位置
    :param metadata: 平台元数据，"{\"tags\": []}"
    :param title: 文档标题
    :return:返回渲染之后的dict
    """
    task_template = {
        "text": f"{text}",
        # 自定义字段
        "start": start,
        "end": end,
        "chunk_title": title,
        "score": score,
        "metaData": metadata,
        "language": "zh-CN",
    }
    return task_template


def create_tasks(project, json_datas):
    tasks = project.import_tasks(json_datas)
    # 批量创建任务
    print(f"批量创建了 {len(tasks)} 个任务")
    return tasks


# 运行
if __name__ == "__main__":
    from src.core.label_studio_client import label_studio_client
    from label_studio_sdk import Client, Project

    label_studio_client: Client
    project: Project = label_studio_client.get_projects(title='切片项目1')[0]
    create_tasks(project, {})
