from flask import render_template
import logging

logger = logging.getLogger(__name__)


def render_annotation_tasks_page():
    """
    渲染标注任务管理页面
    """
    try:
        template_vars = {}
        
        return render_template(
            'annotation_tasks.html',
            **template_vars
        )
    except Exception as e:
        logger.error(f"渲染标注任务管理页面时发生错误：{str(e)}")
        # 返回错误页面或默认内容
        return f"<h1>页面渲染错误：{str(e)}</h1>"
