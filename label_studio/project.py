from label_studio_sdk import Client,Project


def create_project(label_studio_client: Client, question,chunk_size, label_config) -> Project:
    """
    创建项目
    :param label_studio_client:
    :param question:
    :param chunk_size:
    :param label_config:
    :return:
    """
    title = f"{question}_{chunk_size}"
    project = label_studio_client.create_project(
        title=title,
        label_config=label_config,
    )
    return project

