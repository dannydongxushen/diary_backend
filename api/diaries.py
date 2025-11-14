from flask import Blueprint, jsonify

# 创建日记蓝图
diaries_bp = Blueprint('diaries', __name__)

@diaries_bp.route('/', methods=['GET'])
def get_diaries():
    """获取日记列表（待实现）"""
    return jsonify({
        'success': True,
        'message': '日记功能开发中',
        'data': {
            'diaries': []
        }
    })

@diaries_bp.route('/', methods=['POST'])
def create_diary():
    """创建日记（待实现）"""
    return jsonify({
        'success': True,
        'message': '创建日记功能开发中'
    })