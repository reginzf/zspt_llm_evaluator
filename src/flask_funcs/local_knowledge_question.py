# 问题集管理相关路由
from flask import Blueprint, request, jsonify

import logging

from src.flask_funcs.common_utils import validate_required_fields, get_knowledge_base_binding_info, handle_file_upload, \
    generate_unique_id

from src.sql_funs.questions_crud import QuestionsCRUD  # 导入新的QuestionsCRUD类

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
local_knowledge_question_bp = Blueprint('local_knowledge_question', __name__)


@local_knowledge_question_bp.route('/local_knowledge_detail/question_set/create', methods=['POST'])
def create_question_set():
    """创建问题集"""
    try:
        data = request.get_json()
        required_fields = ['knowledge_id', 'set_name', 'set_type']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        knowledge_id = data['knowledge_id']
        set_name = data['set_name']
        set_type = data['set_type']

        question_set_id = generate_unique_id('qs', 8)

        # 创建问题集
        with QuestionsCRUD() as crud:
            result = crud.question_config_create(
                question_id=question_set_id,
                question_name=set_name,
                knowledge_id=knowledge_id
            )

        if result:
            return jsonify({
                'success': True,
                'message': '问题集创建成功',
                'data': {'question_set_id': question_set_id}
            })
        else:
            return jsonify({
                'success': False,
                'message': '问题集创建失败'
            }), 500

    except Exception as e:
        logger.error(f"创建问题集时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'创建问题集时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/set/list', methods=['GET'])
def get_question_set_list():
    """获取问题集列表"""
    try:
        knowledge_id = request.args.get('knowledge_id')

        if not knowledge_id:
            return jsonify({'success': False, 'message': '缺少knowledge_id参数'}), 400

        with QuestionsCRUD() as crud:
            question_sets = crud.question_config_list(knowledge_id=knowledge_id)

        if question_sets:
            # 转换数据格式
            result = []
            for qs in question_sets:
                result.append(crud._question_config_to_json(qs))
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': True,
                'data': []
            })

    except Exception as e:
        logger.error(f"获取问题集列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取问题集列表时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/set/detail', methods=['GET'])
def get_question_set_detail():
    """获取问题集详情"""
    try:
        set_id = request.args.get('set_id')

        if not set_id:
            return jsonify({'success': False, 'message': '缺少set_id参数'}), 400

        with QuestionsCRUD() as crud:
            question_sets = crud.question_config_list(question_id=set_id)

        if question_sets and len(question_sets) > 0:
            result = crud._question_config_to_json(question_sets[0])
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '未找到问题集'
            }), 404

    except Exception as e:
        logger.error(f"获取问题集详情时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取问题集详情时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/set/delete', methods=['DELETE'])
def delete_question_set():
    """删除问题集"""
    try:
        data = request.get_json()
        required_fields = ['set_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        set_id = data['set_id']

        # 删除问题集（注意：这里应该考虑级联删除相关的问题）
        with QuestionsCRUD() as crud:
            # 先删除相关的问题（从各个问题表中删除）
            # 为了简单起见，我们先只删除问题集配置记录
            # 实际应用中可能需要更复杂的级联删除逻辑
            result = crud.question_config_delete(set_id)

        if result:
            return jsonify({
                'success': True,
                'message': '问题集删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '问题集删除失败或问题集不存在'
            }), 500

    except Exception as e:
        logger.error(f"删除问题集时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除问题集时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/set/update', methods=['PUT'])
def update_question_set():
    """更新问题集信息"""
    try:
        data = request.get_json()
        required_fields = ['set_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        set_id = data['set_id']
        set_name = data.get('set_name')
        knowledge_id = data.get('knowledge_id')

        # 更新问题集
        with QuestionsCRUD() as crud:
            result = crud.question_config_update(
                question_id=set_id,
                question_name=set_name,
                knowledge_id=knowledge_id
            )

        if result:
            return jsonify({
                'success': True,
                'message': '问题集更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '问题集更新失败或问题集不存在'
            }), 500

    except Exception as e:
        logger.error(f"更新问题集时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新问题集时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/create', methods=['POST'])
def create_question():
    """创建问题"""
    try:
        data = request.get_json()
        required_fields = ['set_id', 'question_set_type', 'question_type', 'question_content']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        set_id = data['set_id']
        question_set_type = data['question_set_type']
        question_type = data['question_type']
        question_content = data['question_content']
        chunk_ids = data.get('chunk_ids', [])

        # 生成问题ID
        question_id = generate_unique_id('qst', 8)

        question_data = {"question_id": question_id,
                "question_set_id": set_id,
                "question_type": question_type,
                "question_content": question_content,
                "chunk_ids": chunk_ids}
        # 根据问题类型存储到相应表
        result = None
        with QuestionsCRUD() as crud:
            # 将问题写入到对应表中
            if question_set_type == 'basic':
                result = crud.create_basic_question(**question_data)
            elif question_set_type == 'detailed':
                result = crud.create_detailed_question(**question_data)
            elif question_set_type == 'mechanism':
                result = crud.create_mechanism_question(**question_data)
            elif question_set_type == 'thematic':
                result = crud.create_thematic_question(**question_data)
            
            if result:
                # 增加问题集的问题计数（原子操作）
                import psycopg2
                try:
                    # 直接在数据库层面增加计数，避免竞态条件
                    update_query = "UPDATE ai_question_config SET question_count = question_count + 1, updated_at = CURRENT_TIMESTAMP WHERE question_id = %s"
                    crud.cursor.execute(update_query, (set_id,))
                    crud.connection.commit()
                except psycopg2.Error as db_error:
                    crud.connection.rollback()
                    logger.error(f"更新问题计数失败: {db_error}")
                    
        if result:
            return jsonify({
                'success': True,
                'message': '问题创建成功',
                'data': {'question_id': question_id}
            })
        else:
            return jsonify({
                'success': False,
                'message': '问题创建失败'
            }), 500

    except Exception as e:
        logger.error(f"创建问题时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'创建问题时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/list', methods=['GET'])
def get_question_list():
    """获取问题列表"""
    try:
        set_id = request.args.get('set_id')
        question_type = request.args.get('question_type', 'basic')  # 默认为basic

        if not set_id:
            return jsonify({'success': False, 'message': '缺少set_id参数'}), 400

        with QuestionsCRUD() as crud:
            # 根据问题类型获取问题列表
            questions = crud.get_questions_by_type(set_id, question_type)

        if questions:
            # 转换数据格式 - 根据实际表结构调整
            result = []
            for q in questions:
                # 根据实际表结构调整字段索引
                # ai_basic_questions, ai_detailed_questions, ai_mechanism_questions, ai_thematic_questions 表结构:
                # id, question_id, question_set_id, question_type, question_content, chunk_ids, created_at, updated_at
                question_obj = {
                    'id': q[0] if len(q) > 0 else None,
                    'question_id': q[1] if len(q) > 1 else None,
                    'question_set_id': q[2] if len(q) > 2 else None,
                    'question_type': q[3] if len(q) > 3 else None,
                    'question_content': q[4] if len(q) > 4 else None,
                    'chunk_ids': q[5] if len(q) > 5 else [],
                    'created_at': q[6].isoformat() if len(q) > 6 and q[6] else None,
                    'updated_at': q[7].isoformat() if len(q) > 7 and q[7] else None
                }
                result.append(question_obj)
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': True,
                'data': []
            })

    except Exception as e:
        logger.error(f"获取问题列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取问题列表时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/detail', methods=['GET'])
def get_question_detail():
    """获取问题详情"""
    try:
        question_id = request.args.get('question_id')
        question_type = request.args.get('question_type')

        if not question_id or not question_type:
            return jsonify({'success': False, 'message': '缺少question_id或question_type参数'}), 400

        with QuestionsCRUD() as crud:
            # 获取指定类型的问题
            questions = crud.get_questions_by_type(question_id, question_type)

        if questions and len(questions) > 0:
            q = questions[0]
            # 根据实际表结构调整字段索引
            result = {
                'id': q[0] if len(q) > 0 else None,
                'question_id': q[1] if len(q) > 1 else None,
                'question_set_id': q[2] if len(q) > 2 else None,
                'question_type': q[3] if len(q) > 3 else None,
                'question_content': q[4] if len(q) > 4 else None,
                'chunk_ids': q[5] if len(q) > 5 else [],
                'created_at': q[6].isoformat() if len(q) > 6 and q[6] else None,
                'updated_at': q[7].isoformat() if len(q) > 7 and q[7] else None
            }
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '未找到问题'
            }), 404

    except Exception as e:
        logger.error(f"获取问题详情时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取问题详情时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/update', methods=['PUT'])
def update_question():
    """更新问题"""
    try:
        data = request.get_json()
        required_fields = ['question_id', 'question_type']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        question_id = data['question_id']
        question_type = data['question_type']
        question_content = data.get('question_content')
        chunk_ids = data.get('chunk_ids')

        # 使用CRUD类的更新方法
        with QuestionsCRUD() as crud:
            result = crud.update_question_by_type(
                question_id=question_id,
                question_type=question_type,
                question_content=question_content,
                chunk_ids=chunk_ids
            )

            if result:
                return jsonify({
                    'success': True,
                    'message': '问题更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '问题不存在或未被更新'
                }), 404

    except Exception as e:
        logger.error(f"更新问题时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新问题时发生错误: {str(e)}'}), 500


@local_knowledge_question_bp.route('/local_knowledge_detail/question/delete', methods=['DELETE'])
def delete_question():
    """删除问题"""
    try:
        data = request.get_json()
        required_fields = ['question_id', 'question_type']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        question_id = data['question_id']
        question_type = data['question_type']

        # 根据问题类型从相应表中删除
        with QuestionsCRUD() as crud:
            result = crud.delete_question_by_type(question_id, question_type)

            if result:
                return jsonify({
                    'success': True,
                    'message': '问题删除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '问题不存在或删除失败'
                }), 404

    except Exception as e:
        logger.error(f"删除问题时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除问题时发生错误: {str(e)}'}), 500
