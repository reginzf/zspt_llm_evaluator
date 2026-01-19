def create_tasks(project, json_datas, step=10):
    """
    每次创建step个任务，总创建len(json_datas)噶任务
    :param project:
    :param json_datas:
    :param step:
    :return:[task_id...]
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


def get_all_tasks(project):
    """
    获取所有任务
    :param project:
    :return:
    """
    page = 1
    size = 30
    tasks = []
    result = project.get_tasks(page=page, size=size)
    total = result['total']
    tasks.extend(result['tasks'])
    while total > len(tasks):
        page += 1
        result = project.get_tasks(page=page, size=size)
        tasks.extend(result['tasks'])


def get_tasks_with_specific_choice(project, target_choice):
    """
    获取包含特定choice的所有任务

    Args:
        project: Label Studio Project对象
        target_choice: 要查找的choice文本

    Returns:
        list: 包含目标choice的任务列表
    """
    # 获取项目中的所有任务
    try:
        tasks = project.get_tasks()
    except Exception as e:
        print(e)
        return []
    matching_tasks = []

    for task in tasks:
        # 检查每个任务的annotations
        if 'annotations' in task and task['annotations']:
            for annotation in task['annotations']:
                if 'result' in annotation:
                    for result in annotation['result']:
                        # 检查是否是choices类型
                        if (result.get('type') == 'choices' and
                                'value' in result and
                                'choices' in result['value']):

                            # 检查是否包含目标choice
                            if target_choice in result['value']['choices']:
                                matching_tasks.append(task)
                                break  # 找到就跳出内层循环
                    else:
                        continue
                    break  # 找到就跳出外层循环
    return matching_tasks


if __name__ == "__main__":
    from label_studio_sdk import Client, Project

    label_studio_client: Client
    project: Project = label_studio_client.get_projects(title='OSPFv2_RFC2328_Detailed_500_10')[0]
    tasks = get_tasks_with_specific_choice(project, "在广播网络中，OSPF路由器如何发现邻居？")
    print(tasks)
