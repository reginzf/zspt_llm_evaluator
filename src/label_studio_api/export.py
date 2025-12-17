import json
from label_studio_sdk import Project


# 将任务数据转换为自定义的格式

def transform_to_custom_format(tasks):
    """将原始数据转换为自定义格式"""
    custom_data = []

    for task in tasks:
        # 提取任务基本信息
        task_id = task.get('id')
        data = task.get('data', {})
        annotations = task.get('annotations', [])

        # 构建自定义格式
        custom_task = {
            # 元数据
            "metadata": {
                "task_id": task_id,
                "project_id": project.id,
            },
            # 原始数据（可选择性包含）
            "source_data": {
                "text": data.get('text', ''),
                "size": data.get('size', ''),
                "fileName": data.get('fileName', '')
            },

            # 标注结果（自定义结构）
            "annotations": []
        }

        # 处理每个标注
        for ann in annotations:
            if ann.get('result'):
                custom_ann = {
                    "result": ann['result']  # 保留原始结果
                }
                custom_task["annotations"].append(custom_ann)

        custom_data.append(custom_task)

    return custom_data


def export_custom_json_format(project: Project, export_type='JSON'):
    raw_data = project.export_tasks(export_type=export_type)

    # 转换数据
    custom_format_data = transform_to_custom_format(raw_data)
    project_info = project.title.split('_')
    chunk_size = int(project_info[-2])
    chunk_overlap = int(project_info[-1])
    project_title = '_'.join(project_info[:-2])
    pro_data = {"doc_name": project_title, "project_id": project.id,
                "chunk_size": chunk_size, "chunk_overlap": chunk_overlap, "project_data": custom_format_data}
    # 保存为JSON文件

    output_file = f"{project.title}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pro_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"自定义格式已导出到: {output_file}")
    print(f"共导出 {len(custom_format_data)} 个任务")
    return custom_format_data


if __name__ == '__main__':
    from label_studio_api.label_studio_client import label_studio_client
    project = label_studio_client.get_projects(title='OSPFv2_RFC2328_Detailed_400_10')[0]
    export_custom_json_format(project)
