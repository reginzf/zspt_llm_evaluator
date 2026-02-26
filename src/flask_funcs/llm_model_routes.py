# -*- coding: utf-8 -*-
"""
LLM模型管理API路由模块
"""
from flask import Blueprint, request, jsonify, render_template
import logging

from datetime import datetime


from src.sql_funs.llm_model_crud import LLMModelManager
from src.sql_funs.llm_evaluation_report_crud import LLMEvaluationReportManager
from src.sql_funs.ai_qa_data_group_crud import AIQADataGroupManager

logger = logging.getLogger(__name__)

# 创建蓝图
llm_model_bp = Blueprint('llm_model', __name__)


# ==================== 页面路由 ====================

@llm_model_bp.route('/llm/models')
def llm_models_page():
    """LLM模型管理页面"""
    return render_template('llm_models.html')


@llm_model_bp.route('/llm/models/<string:model_name>')
def llm_model_detail_page(model_name):
    """LLM模型详情页面"""
    return render_template('llm_model_detail.html', model_name=model_name)


# ==================== API路由 - 模型管理 ====================

@llm_model_bp.route('/api/llm/models', methods=['GET'])
def get_llm_models():
    """
    获取LLM模型列表
    
    Query Parameters:
        page: 页码，默认1
        limit: 每页数量，默认20
        type: 模型类型筛选
        status: 状态筛选
        keyword: 关键词搜索
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        model_type = request.args.get('type')
        status = request.args.get('status')
        keyword = request.args.get('keyword')
        
        offset = (page - 1) * limit
        
        with LLMModelManager() as manager:
            models = manager.list_models(
                model_type=model_type,
                status=status,
                keyword=keyword,
                limit=limit,
                offset=offset
            )
            total = manager.count_models(
                model_type=model_type,
                status=status,
                keyword=keyword
            )
        
        pages = (total + limit - 1) // limit if limit > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages,
                'rows': models
            }
        })
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取模型列表失败: {str(e)}'
        }), 500


@llm_model_bp.route('/api/llm/models/<string:model_name>', methods=['GET'])
def get_llm_model(model_name):
    """获取单个模型详情"""
    try:
        with LLMModelManager() as manager:
            model = manager.get_model_by_name(model_name)
            
            if not model:
                return jsonify({
                    'success': False,
                    'message': f'模型不存在: {model_name}'
                }), 404
            
            # 获取评估报告列表
            with LLMEvaluationReportManager() as report_manager:
                reports = report_manager.list_reports(model_name=model_name, limit=10)
                report_count = report_manager.count_reports(model_name=model_name)
            
            return jsonify({
                'success': True,
                'data': {
                    'config': model,
                    'connection_status': model.get('status') == 'connected',
                    'last_evaluation': model.get('last_check'),
                    'evaluation_count': report_count,
                    'recent_reports': reports
                }
            })
            
    except Exception as e:
        logger.error(f"获取模型详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取模型详情失败: {str(e)}'
        }), 500


@llm_model_bp.route('/api/llm/models', methods=['POST'])
def create_llm_model():
    """创建LLM模型配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        # 验证必填字段
        required_fields = ['name', 'type', 'api_key', 'api_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        name = data['name']
        
        with LLMModelManager() as manager:
            # 检查名称是否已存在
            if manager.model_exists(name):
                return jsonify({
                    'success': False,
                    'message': f'模型名称已存在: {name}'
                }), 400
            
            # 创建模型
            model_id = manager.create_model(
                name=name,
                model_type=data['type'],
                api_key=data['api_key'],
                api_url=data['api_url'],
                model=data.get('model'),
                temperature=data.get('temperature', 0.7),
                max_tokens=data.get('max_tokens', 2048),
                timeout=data.get('timeout', 30),
                version=data.get('version')
            )
            
            if model_id:
                return jsonify({
                    'success': True,
                    'message': '模型创建成功',
                    'data': {'id': model_id}
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '模型创建失败'
                }), 500
                
    except Exception as e:
        logger.error(f"创建模型失败: {e}")
        return jsonify({
            'success': False,
            'message': f'创建模型失败: {str(e)}'
        }), 500


@llm_model_bp.route('/api/llm/models/<string:model_name>', methods=['PUT'])
def update_llm_model(model_name):
    """更新LLM模型配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        with LLMModelManager() as manager:
            # 获取模型
            model = manager.get_model_by_name(model_name)
            if not model:
                return jsonify({
                    'success': False,
                    'message': f'模型不存在: {model_name}'
                }), 404
            
            # 更新模型
            success = manager.update_model(model['id'], **data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '模型更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '模型更新失败'
                }), 500
                
    except Exception as e:
        logger.error(f"更新模型失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新模型失败: {str(e)}'
        }), 500


@llm_model_bp.route('/api/llm/models/<string:model_name>', methods=['DELETE'])
def delete_llm_model(model_name):
    """删除LLM模型"""
    try:
        with LLMModelManager() as manager:
            # 获取模型
            model = manager.get_model_by_name(model_name)
            if not model:
                return jsonify({
                    'success': False,
                    'message': f'模型不存在: {model_name}'
                }), 404
            
            # 删除模型（软删除）
            success = manager.delete_model(model['id'])
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '模型删除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '模型删除失败'
                }), 500
                
    except Exception as e:
        logger.error(f"删除模型失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除模型失败: {str(e)}'
        }), 500


@llm_model_bp.route('/api/llm/models/<string:model_name>/check', methods=['POST'])
def check_llm_model_connection(model_name):
    """检查模型连通性"""
    try:
        with LLMModelManager() as manager:
            # 获取模型配置
            model = manager.get_model_by_name(model_name)
            if not model:
                return jsonify({
                    'success': False,
                    'message': f'模型不存在: {model_name}'
                }), 404
            
            # 构建agent配置
            agent_config = {
                'name': model['name'],
                'type': model['type'],
                'api_key': model['api_key'],
                'api_url': model['api_url'],
                'model': model.get('model'),
                'temperature': float(model.get('temperature', 0.7)),
                'max_tokens': model.get('max_tokens', 2048),
                'timeout': model.get('timeout', 30),
                'version': model.get('version')
            }
            
            try:
                # 创建agent并测试连接
                from src.llm.llm_agent_basic import create_agent
                agent = create_agent(agent_config)
                success, message = agent.test_connection()
                
                # 更新状态
                status = 'connected' if success else 'error'
                manager.update_status(model['id'], status)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': '模型连接正常',
                        'data': {'status': status}
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'模型连接失败: {message}',
                        'data': {'status': status}
                    }), 500
                    
            except Exception as e:
                status = 'error'
                manager.update_status(model['id'], status)
                return jsonify({
                    'success': False,
                    'message': f'模型连接失败: {str(e)}',
                    'data': {'status': status}
                }), 500
                
    except Exception as e:
        logger.error(f"检查模型连通性失败: {e}")
        return jsonify({
            'success': False,
            'message': f'检查模型连通性失败: {str(e)}'
        }), 500


# ==================== API路由 - 评估执行 ====================

@llm_model_bp.route('/api/llm/models/<string:model_name>/evaluate', methods=['POST'])
def start_evaluation(model_name):
    """启动评估任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        group_id = data.get('group_id')
        if not group_id:
            return jsonify({
                'success': False,
                'message': '缺少必填字段: group_id'
            }), 400
        
        # TODO: 实现实际的评估任务启动
        # 这里先返回模拟响应
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return jsonify({
            'success': True,
            'message': '评估任务已启动',
            'data': {
                'task_id': task_id,
                'status': 'running'
            }
        })
        
    except Exception as e:
        logger.error(f"启动评估任务失败: {e}")
        return jsonify({
            'success': False,
            'message': f'启动评估任务失败: {str(e)}'
        }), 500


@llm_model_bp.route('/api/llm/evaluation/<string:task_id>/progress', methods=['GET'])
def get_evaluation_progress(task_id):
    """获取评估进度"""
    try:
        # TODO: 实现实际的进度查询
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'running',
                'progress': 50,
                'current_step': 'evaluating',
                'processed': 50,
                'total': 100
            }
        })
        
    except Exception as e:
        logger.error(f"获取评估进度失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取评估进度失败: {str(e)}'
        }), 500


# ==================== API路由 - 报告管理 ====================

@llm_model_bp.route('/api/llm/models/<string:model_name>/reports', methods=['GET'])
def get_model_reports(model_name):
    """获取模型的评估报告列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        offset = (page - 1) * limit
        
        with LLMEvaluationReportManager() as manager:
            reports = manager.list_reports(model_name=model_name, limit=limit, offset=offset)
            total = manager.count_reports(model_name=model_name)
        
        pages = (total + limit - 1) // limit if limit > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages,
                'rows': reports
            }
        })
        
    except Exception as e:
        logger.error(f"获取报告列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取报告列表失败: {str(e)}'
        }), 500
