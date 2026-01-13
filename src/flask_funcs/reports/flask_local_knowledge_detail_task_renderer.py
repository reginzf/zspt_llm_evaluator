from flask import render_template
import logging

logger = logging.getLogger(__name__)


def render_task_metric_page(knowledge_id):
    """
    渲染任务指标管理页面
    """
    try:
        # 这里可以添加业务逻辑，比如获取特定知识库的任务列表等
        template_vars = {
            'knowledge_id': knowledge_id
        }
        
        return render_template(
            'local_knowledge_detail_task.html',
            **template_vars
        )
    except Exception as e:
        logger.error(f"渲染任务指标管理页面时发生错误: {str(e)}")
        # 返回错误页面或默认内容
        return f"<h1>页面渲染错误: {str(e)}</h1>"