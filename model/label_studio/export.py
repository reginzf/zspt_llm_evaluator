import json
from label_studio_sdk import Project
from datetime import datetime


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
                "export_timestamp": datetime.now().isoformat(),
                "project_id": project.id,
                "data_fields": list(data.keys())
            },

            # 原始数据（可选择性包含）
            "source_data": {
                "text": data.get('text', ''),
                "image_url": data.get('image', ''),
                "audio_url": data.get('audio', ''),
                # 自定义字段
                "chunk_start": data.get('chunk_start'),
                "chunk_size": data.get('chunk_size'),
                "custom_fields": {k: v for k, v in data.items()
                                  if k not in ['text', 'image', 'audio']}
            },

            # 标注结果（自定义结构）
            "annotations": []
        }
        print(annotations)
        # 处理每个标注
        for ann in annotations:
            if ann.get('result'):
                custom_ann = {
                    "annotation_id": ann.get('id'),
                    "annotator": ann.get('completed_by', {}),
                    "created_at": ann.get('created_at'),
                    "updated_at": ann.get('updated_at'),
                    "lead_time": ann.get('lead_time'),
                    "result_summary": extract_result_summary(ann['result']),
                    "raw_result": ann['result']  # 保留原始结果
                }
                custom_task["annotations"].append(custom_ann)

        custom_data.append(custom_task)

    return custom_data


def extract_result_summary(results):
    """从标注结果中提取摘要信息"""
    summary = {
        "total_regions": len(results),
        "label_counts": {},
        "region_types": set()
    }

    for result in results:
        value = result.get('value', {})
        labels = value.get('choices', []) or value.get('labels', [])

        if isinstance(labels, list):
            for label in labels:
                summary["label_counts"][label] = summary["label_counts"].get(label, 0) + 1

        # 记录区域类型
        if 'from_name' in result:
            summary["region_types"].add(result['from_name'])

    summary["region_types"] = list(summary["region_types"])
    return summary


def export_custom_json_format(project: Project, export_type='JSON'):
    raw_data = project.export_tasks(export_type=export_type)

    # 转换数据
    custom_format_data = transform_to_custom_format(raw_data)

    # 保存为JSON文件
    output_file = f"custom_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(custom_format_data, f, ensure_ascii=False, indent=2,
                  default=str)  # 处理日期时间对象

    print(f"自定义格式已导出到: {output_file}")
    print(f"共导出 {len(custom_format_data)} 个任务")

    return custom_format_data


if __name__ == '__main__':
    from model.label_studio.label_studio_client import label_studio_client

    project = label_studio_client.get_projects(title='切片项目1')[0]
    export_custom_json_format(project)
