# -*- coding: utf-8 -*-
"""
LLM模型管理API路由模块
"""
import logging
import threading
import uuid
import os
import tempfile

from flask import Blueprint, request, jsonify
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from src.llm.api_agent_evaluator import LLMEvaluator
from src.llm.data_loaders import QuestionAnswerPair
from src.sql_funs.ai_qa_data_crud import AIQADataManager

from src.sql_funs.llm_model_crud import LLMModelManager
from src.sql_funs.llm_evaluation_report_crud import LLMEvaluationReportManager
from src.sql_funs.ai_qa_data_group_crud import AIQADataGroupManager
from src.utils.minio_client import get_llm_evaluation_client

logger = logging.getLogger(__name__)

# 创建蓝图
llm_model_bp = Blueprint('llm_model', __name__)

# 全局任务管理器（用于跟踪后台评估任务）
_evaluation_tasks: Dict[str, Dict[str, Any]] = {}


def run_evaluation_task(task_id: str, model_name: str, model_config: dict,
                        group_id: int, group_name: str, offset: int, limit: int,
                        parallel: bool, max_workers: int, match_types: dict):
    """
    在后台线程中运行评估任务
    
    Args:
        task_id: 任务ID
        model_name: 模型名称
        model_config: 模型配置
        group_id: 问答对组ID
        group_name: 问答对组名称
        offset: 起始位置
        limit: 评估数量
        parallel: 是否并行处理
        max_workers: 并行工作数
        match_types: 匹配类型配置
    """
    try:
        # 更新任务状态为运行中
        _evaluation_tasks[task_id]['status'] = 'running'
        _evaluation_tasks[task_id]['progress'] = 10
        _evaluation_tasks[task_id]['message'] = '正在初始化评估器...'

        # 导入评估器
        output_dir = Path('./evaluation_results')
        output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化评估器，传入 match_types
        evaluator = LLMEvaluator(
            output_dir=str(output_dir),
            match_types=match_types
        )

        _evaluation_tasks[task_id]['progress'] = 20
        _evaluation_tasks[task_id]['message'] = '正在加载问答对数据...'

        # 加载问答对数据
        with AIQADataManager() as qa_manager:
            qa_pairs = qa_manager.list_qa_data(
                group_id=group_id,
                limit=limit,
                offset=offset
            )

        if not qa_pairs:
            _evaluation_tasks[task_id]['status'] = 'failed'
            _evaluation_tasks[task_id]['message'] = '没有找到问答对数据'
            return

        # 将数据库记录转换为评估器需要的格式
        evaluator.qa_pairs = []
        for qa in qa_pairs:
            # 处理answers字段：数据库中存储为字典格式 {'text': [...], 'answer_start': [...]}
            answers_data = qa.get('answers', {})
            if isinstance(answers_data, dict):
                # 从字典中提取text列表
                answers = answers_data.get('text', [])
                if not isinstance(answers, list):
                    answers = [answers] if answers else []
            elif isinstance(answers_data, list):
                answers = answers_data
            elif isinstance(answers_data, str):
                answers = [answers_data] if answers_data else []
            else:
                answers = []
            
            qa_pair = QuestionAnswerPair(
                id=qa.get('id', 0),
                question=qa.get('question', ''),
                answers=answers,
                context=qa.get('context', ''),
                metadata={
                    'group_id': group_id,
                    'source': qa.get('source_dataset', '')
                }
            )
            evaluator.qa_pairs.append(qa_pair)

        _evaluation_tasks[task_id]['progress'] = 30
        _evaluation_tasks[task_id]['message'] = '正在初始化LLM Agent...'
        _evaluation_tasks[task_id]['total'] = len(evaluator.qa_pairs)

        # 创建Agent并添加到评估器
        agent_config = {
            'name': model_name,
            'type': model_config['type'],
            'api_key': model_config['api_key'],
            'api_url': model_config['api_url'],
            'model': model_config.get('model'),
            'temperature': float(model_config.get('temperature', 0.7)),
            'max_tokens': model_config.get('max_tokens', 2048),
            'timeout': model_config.get('timeout', 30),
            'version': model_config.get('version')
        }

        success, message = evaluator.add_agent(agent_config, test_connection=True)
        if not success:
            _evaluation_tasks[task_id]['status'] = 'failed'
            _evaluation_tasks[task_id]['message'] = f'Agent初始化失败: {message}'
            return

        _evaluation_tasks[task_id]['progress'] = 40
        _evaluation_tasks[task_id]['message'] = '正在执行评估...'

        # 执行评估
        result = evaluator.evaluate_agent(
            agent_name=model_name,
            sample_size=None,  # 使用全部加载的数据
            parallel=parallel,
            max_workers=max_workers,
            retry_attempts=3,
            show_progress=False,  # 后台任务不显示进度条
            match_types=match_types
        )

        _evaluation_tasks[task_id]['progress'] = 80
        _evaluation_tasks[task_id]['message'] = '正在保存评估结果...'

        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"evaluation_{model_name}_{timestamp}.json"
        
        # 构建MinIO对象名称
        minio_object_name = f"reports/{model_name}/{report_filename}"
        
        # 将 numpy 类型转换为 Python 原生类型
        def convert_to_float(value):
            """将 numpy 类型或其他数值转换为 Python float"""
            if value is None:
                return None
            if hasattr(value, 'item'):  # numpy 类型
                return float(value.item())
            return float(value)

        # 保存详细结果到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_report_path = tmp_file.name
        
        try:
            # 使用评估器保存结果到临时文件
            evaluator.save_results(filename=os.path.basename(tmp_report_path), detailed=True)
            
            # 读取保存的文件内容并写入临时文件
            local_report_path = os.path.join(evaluator.output_dir, os.path.basename(tmp_report_path))
            with open(local_report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            with open(tmp_report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # 上传到MinIO
            minio_client = get_llm_evaluation_client()
            upload_success = minio_client.upload_file(tmp_report_path, minio_object_name)
            
            if not upload_success:
                raise Exception("上传报告到MinIO失败")
            
            logger.info(f"评估报告已上传到MinIO: {minio_object_name}")
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_report_path):
                os.unlink(tmp_report_path)
            # 清理评估器生成的本地文件
            if os.path.exists(local_report_path):
                os.unlink(local_report_path)

        # 获取指标数据（转换为 Python 原生类型）
        metrics = result.metrics
        exact_match = convert_to_float(metrics.exact_match)
        f1_score = convert_to_float(metrics.f1_score)
        semantic_similarity = convert_to_float(metrics.semantic_similarity)
        avg_inference_time = convert_to_float(metrics.avg_inference_time)

        # 保存到数据库，report_path存储MinIO对象名称
        with LLMEvaluationReportManager() as report_manager:
            with LLMModelManager() as model_manager:
                model = model_manager.get_model_by_name(model_name)
                model_id = model['id'] if model else None

            report_id = report_manager.create_report(
                report_name=f"{model_name} - {group_name} - {timestamp}",
                model_name=model_name,
                model_id=model_id,
                group_id=group_id,
                group_name=group_name,
                report_path=minio_object_name,  # 存储MinIO对象名称
                qa_count=int(metrics.total_samples) if metrics.total_samples else 0,
                qa_offset=int(offset),
                qa_limit=int(limit),
                exact_match=exact_match,
                f1_score=f1_score,
                semantic_similarity=semantic_similarity,
                avg_inference_time=avg_inference_time,
                evaluation_config={
                    'match_types': match_types,
                    'parallel': parallel,
                    'max_workers': max_workers,
                    'offset': offset,
                    'limit': limit
                },
                status='completed'
            )

        # 更新任务状态为完成
        _evaluation_tasks[task_id]['status'] = 'completed'
        _evaluation_tasks[task_id]['progress'] = 100
        _evaluation_tasks[task_id]['message'] = '评估完成'
        _evaluation_tasks[task_id]['report_id'] = report_id
        _evaluation_tasks[task_id]['metrics'] = {
            'exact_match': exact_match,
            'f1_score': f1_score,
            'semantic_similarity': semantic_similarity,
            'avg_inference_time': avg_inference_time,
            'total_samples': int(metrics.total_samples) if metrics.total_samples else 0,
            'successful_predictions': int(metrics.successful_predictions) if metrics.successful_predictions else 0,
            'failed_predictions': int(metrics.failed_predictions) if metrics.failed_predictions else 0
        }

        logger.info(f"评估任务 {task_id} 完成")

    except Exception as e:
        logger.error(f"评估任务 {task_id} 执行失败: {e}")
        _evaluation_tasks[task_id]['status'] = 'failed'
        _evaluation_tasks[task_id]['message'] = f'评估失败: {str(e)}'
        _evaluation_tasks[task_id]['error'] = str(e)


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

        # 获取模型配置
        with LLMModelManager() as manager:
            model = manager.get_model_by_name(model_name)
            if not model:
                return jsonify({
                    'success': False,
                    'message': f'模型不存在: {model_name}'
                }), 404

            # 检查模型状态
            if model.get('status') != 'connected':
                return jsonify({
                    'success': False,
                    'message': '模型未连接，请先检测模型连通性'
                }), 400

        # 获取问答对组信息
        with AIQADataGroupManager() as group_manager:
            group = group_manager.get_group_by_id(group_id)
            if not group:
                return jsonify({
                    'success': False,
                    'message': f'问答对组不存在: {group_id}'
                }), 404
            group_name = group.get('name', 'Unknown')

        # 获取评估参数
        offset = int(data.get('offset', 0))
        limit = int(data.get('limit', 100))
        parallel = data.get('parallel', False)
        max_workers = int(data.get('max_workers', 4))
        match_types = data.get('match_types', {})

        # 生成任务ID
        task_id = f"task_{uuid.uuid4().hex[:16]}"

        # 初始化任务状态
        _evaluation_tasks[task_id] = {
            'id': task_id,
            'model_name': model_name,
            'group_id': group_id,
            'status': 'pending',
            'progress': 0,
            'message': '等待开始...',
            'created_at': datetime.now().isoformat(),
            'total': 0,
            'processed': 0
        }

        # 启动后台线程执行评估
        thread = threading.Thread(
            target=run_evaluation_task,
            args=(
                task_id, model_name, model,
                group_id, group_name, offset, limit,
                parallel, max_workers, match_types
            ),
            daemon=True
        )
        thread.start()

        logger.info(f"评估任务 {task_id} 已启动: 模型={model_name}, 组={group_name}")

        return jsonify({
            'success': True,
            'message': '评估任务已启动',
            'data': {
                'task_id': task_id,
                'status': 'pending'
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
        task = _evaluation_tasks.get(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': task.get('status', 'unknown'),
                'progress': task.get('progress', 0),
                'message': task.get('message', ''),
                'processed': task.get('processed', 0),
                'total': task.get('total', 0),
                'metrics': task.get('metrics'),
                'report_id': task.get('report_id')
            }
        })

    except Exception as e:
        logger.error(f"获取评估进度失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取评估进度失败: {str(e)}'
        }), 500


@llm_model_bp.route('/api/llm/evaluation/tasks', methods=['GET'])
def list_evaluation_tasks():
    """获取评估任务列表"""
    try:
        # 过滤和返回任务列表
        tasks = []
        for task_id, task in _evaluation_tasks.items():
            tasks.append({
                'task_id': task_id,
                'model_name': task.get('model_name'),
                'group_id': task.get('group_id'),
                'status': task.get('status'),
                'progress': task.get('progress'),
                'message': task.get('message'),
                'created_at': task.get('created_at')
            })

        # 按创建时间倒序排序
        tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return jsonify({
            'success': True,
            'data': tasks
        })

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取任务列表失败: {str(e)}'
        }), 500


# ==================== 页面路由 - LLM评估报告查看 ====================

@llm_model_bp.route('/llm/report/<path:filename>')
def view_llm_evaluation_report(filename):
    """
    查看LLM评估报告页面
    
    从 MinIO 加载LLM评估报告并渲染为HTML页面
    """
    from src.utils.pub_funs import read_json_file
    from src.flask_funcs.reports.flask_llm_evaluation_renderer import LLMEvaluationRenderer

    try:
        # 标准化路径：将URL中的正斜杠转换为正斜杠（MinIO使用正斜杠）
        filename = filename.replace(os.sep, '/')
        
        logger.info(f"尝试从MinIO加载评估报告: {filename}")

        # 从MinIO下载报告到临时文件
        minio_client = get_llm_evaluation_client()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_report_path = tmp_file.name
        
        try:
            # 下载报告文件
            download_success = minio_client.download_file(filename, tmp_report_path)
            
            if not download_success:
                logger.warning(f"MinIO中不存在评估报告: {filename}")
                return f"报告文件不存在: {filename}", 404
            
            # 加载评估数据
            evaluation_data = read_json_file(tmp_report_path)
            if not evaluation_data:
                logger.warning(f"无法加载评估报告数据: {filename}")
                return f"无法加载评估报告: {filename}", 404

            # 创建LLM评估报告渲染器
            renderer = LLMEvaluationRenderer()

            # 渲染报告页面
            html_content = renderer.render_evaluation_report(evaluation_data, filename)

            logger.info(f"成功渲染LLM评估报告: {filename}")
            return html_content
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_report_path):
                os.unlink(tmp_report_path)

    except Exception as e:
        logger.error(f"处理LLM评估报告 {filename} 时发生错误: {str(e)}", exc_info=True)
        return f"处理报告时发生错误: {str(e)}", 500


# ==================== API路由 - 报告管理 ====================

@llm_model_bp.route('/api/llm/models/<string:model_name>/reports', methods=['GET'])
def get_model_reports(model_name):
    """获取模型的评估报告列表"""
    try:
        # Check if simple list mode is requested (no pagination)
        simple_mode = request.args.get('simple', 'false').lower() == 'true'
        
        with LLMEvaluationReportManager() as manager:
            if simple_mode:
                # Simple mode: return all reports as array
                reports = manager.list_reports(model_name=model_name, limit=1000, offset=0)
                # Map database field names to frontend expected field names
                mapped_reports = []
                for report in reports:
                    mapped_report = {
                        'id': report.get('id'),
                        'filename': report.get('report_name'),
                        'model_name': report.get('model_name'),
                        'created_at': report.get('created_at'),
                        'path': report.get('report_path'),
                        'status': report.get('status'),
                        'exact_match': report.get('exact_match'),
                        'f1_score': report.get('f1_score'),
                        'semantic_similarity': report.get('semantic_similarity'),
                        'avg_inference_time': report.get('avg_inference_time')
                    }
                    mapped_reports.append(mapped_report)
                return jsonify({
                    'success': True,
                    'data': mapped_reports
                })
            else:
                # Pagination mode: return paginated response
                page = int(request.args.get('page', 1))
                limit = int(request.args.get('limit', 20))
                offset = (page - 1) * limit
                
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


@llm_model_bp.route('/api/llm/reports/<int:report_id>', methods=['DELETE'])
def delete_evaluation_report(report_id: int):
    """
    删除评估报告
    
    Args:
        report_id: 报告ID
        
    Returns:
        JSON: {success: bool, message: str}
    """
    try:
        logger.info(f"开始删除评估报告: ID={report_id}")
        
        # 获取报告信息
        with LLMEvaluationReportManager() as report_manager:
            report = report_manager.get_report_by_id(report_id)
            
            if not report:
                logger.warning(f"报告不存在: ID={report_id}")
                return jsonify({
                    'success': False,
                    'message': f'报告不存在: ID={report_id}'
                }), 404
            
            report_path = report.get('report_path')
            logger.info(f"找到报告: ID={report_id}, path={report_path}")
            
            # 删除MinIO中的文件（如果存在report_path）
            if report_path:
                try:
                    minio_client = get_llm_evaluation_client()
                    
                    # 检查文件是否存在
                    if minio_client.file_exists(report_path):
                        # 删除文件
                        delete_success = minio_client.delete_file(report_path)
                        if delete_success:
                            logger.info(f"MinIO文件删除成功: {report_path}")
                        else:
                            logger.warning(f"MinIO文件删除失败: {report_path}")
                    else:
                        logger.warning(f"MinIO文件不存在，跳过删除: {report_path}")
                except Exception as minio_error:
                    # MinIO删除失败，记录日志但继续删除数据库记录
                    logger.error(f"删除MinIO文件时出错: {minio_error}", exc_info=True)
            else:
                logger.info(f"报告没有关联的文件路径，跳过MinIO删除")
            
            # 删除数据库记录
            delete_success = report_manager.delete_report(report_id)
            
            if delete_success:
                logger.info(f"评估报告删除成功: ID={report_id}")
                return jsonify({
                    'success': True,
                    'message': '报告删除成功'
                })
            else:
                logger.error(f"删除数据库记录失败: ID={report_id}")
                return jsonify({
                    'success': False,
                    'message': '删除数据库记录失败'
                }), 500
                
    except Exception as e:
        logger.error(f"删除评估报告失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'删除评估报告失败: {str(e)}'
        }), 500
