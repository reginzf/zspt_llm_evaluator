def create_tasks(project, json_datas, step=10):
    """
    每次创建step个任务，总创建len(json_datas)噶任务
    :param project:
    :param json_datas:
    :param step:
    :return:
    """
    # 批量创建任务
    len_tasks = len(json_datas)
    res = []
    left = 0
    right = min(10, len_tasks)
    while right < len_tasks + 1:
        if left == right: break
        res.extend(project.import_tasks(json_datas[left:right]))
        left = right
        right = min(right + step, len_tasks)

    print(f"批量创建了 {len(json_datas)} 个任务")
    return res


# 运行
if __name__ == "__main__":
    from label_studio_sdk import Client, Project

    label_studio_client: Client
    project: Project = label_studio_client.get_projects(title='切片项目1')[0]
    create_tasks(project, {})
