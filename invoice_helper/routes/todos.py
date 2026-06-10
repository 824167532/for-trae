"""
待办路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from services.todo_service import TodoService

todos_bp = Blueprint('todos', __name__, url_prefix='/api/todos')
todo_service = TodoService()


@todos_bp.route('', methods=['GET'])
def get_todos():
    """获取待办列表"""
    send_status = request.args.get('send_status', 'unsent')
    customer_id = request.args.get('customer_id', type=int)
    business_month = request.args.get('business_month')
    
    todos = todo_service.get_all(send_status, customer_id, business_month)
    return jsonify(todos)


@todos_bp.route('', methods=['POST'])
def create_todo():
    """创建待办"""
    data = request.get_json()
    customer_id = data.get('customer_id')
    business_month = data.get('business_month')
    amount = data.get('amount')
    filename = data.get('filename')
    image_data = data.get('image_data')
    
    if not customer_id or not business_month or not filename or not image_data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    # 检查重复
    if todo_service.check_duplicate(customer_id, business_month):
        return jsonify({'error': '该客户该月份已存在待办', 'duplicate': True}), 400
    
    todo = todo_service.create(customer_id, business_month, amount, filename, image_data)
    if todo:
        return jsonify(todo)
    else:
        return jsonify({'error': '创建失败'}), 400


@todos_bp.route('/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """更新待办"""
    data = request.get_json()
    business_month = data.get('business_month')
    amount = data.get('amount')
    
    todo = todo_service.update(todo_id, business_month, amount)
    if todo:
        return jsonify(todo)
    else:
        return jsonify({'error': '更新失败'}), 400


@todos_bp.route('/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """删除待办"""
    data = request.get_json() or {}
    delete_file = data.get('delete_file', False)
    
    success = todo_service.delete(todo_id, delete_file)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': '删除失败'}), 400


@todos_bp.route('/refresh-status', methods=['POST'])
def refresh_status():
    """刷新开票状态"""
    updated_count = todo_service.refresh_invoice_status()
    return jsonify({'success': True, 'updated_count': updated_count})


@todos_bp.route('/<int:todo_id>/mark-sent', methods=['POST'])
def mark_sent(todo_id):
    """标记已发送"""
    success = todo_service.mark_sent(todo_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': '标记失败，请确认开票状态为已开票且发送状态为未发送'}), 400


@todos_bp.route('/check-duplicate', methods=['POST'])
def check_duplicate():
    """检查重复待办"""
    data = request.get_json()
    customer_id = data.get('customer_id')
    business_month = data.get('business_month')
    
    if not customer_id or not business_month:
        return jsonify({'error': '缺少必要参数'}), 400
    
    is_duplicate = todo_service.check_duplicate(customer_id, business_month)
    return jsonify({'duplicate': is_duplicate})


@todos_bp.route('/missing-current-month', methods=['GET'])
def missing_current_month():
    """获取当月无待办的客户"""
    missing = todo_service.get_missing_current_month()
    return jsonify(missing)


@todos_bp.route('/history', methods=['GET'])
def get_history():
    """获取历史记录"""
    customer_id = request.args.get('customer_id', type=int)
    business_month = request.args.get('business_month')
    send_status = request.args.get('send_status')
    
    history = todo_service.get_history(customer_id, business_month, send_status)
    return jsonify(history)