def create_tasks(project, json_datas):
    tasks = project.import_tasks(json_datas)
    # 批量创建任务
    print(f"批量创建了 {len(tasks)} 个任务")
    return tasks


# 运行
if __name__ == "__main__":
    from label_studio_sdk import Client, Project

    label_studio_client: Client
    project: Project = label_studio_client.get_projects(title='切片项目1')[0]
    create_tasks(project, {})
