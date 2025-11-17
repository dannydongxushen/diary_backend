# api/diaries.py
from flask import Blueprint, request, jsonify, current_app
import logging
import jwt
from database.config import query_one, query_all

logger = logging.getLogger(__name__)
diaries_bp = Blueprint('diaries', __name__)

def get_current_user_id():
    """
    从JWT token中获取当前登录用户的ID
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None, '缺少认证令牌'
        
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id'], None
    except jwt.ExpiredSignatureError:
        return None, '令牌已过期'
    except jwt.InvalidTokenError:
        return None, '无效令牌'
    except Exception as e:
        logger.error(f"解析用户ID失败: {e}")
        return None, '获取用户信息失败'

@diaries_bp.route('/', methods=['GET'])
def get_diaries():
    """获取用户日记列表 - 最简洁版"""
    try:
        user_id, error = get_current_user_id()
        if error:
            return jsonify({'success': False, 'error': error}), 401
        
        # 查询用户日记数量
        count_result = query_one(
            "SELECT COUNT(*) as total FROM diaries WHERE user_id = %s", 
            (user_id,)
        )
        
        # 如果查询失败或表不存在，当作没有日记处理
        if not count_result:
            diary_count = 0
        else:
            diary_count = count_result['total']
        
        # 如果有日记，获取日记列表
        if diary_count > 0:
            diaries = query_all("""
                SELECT diary_id, title, content, created_at
                FROM diaries 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            
            diaries_list = []
            for diary in diaries:
                diaries_list.append({
                    'id': diary['diary_id'],
                    'title': diary['title'],
                    'content': diary['content'],
                    'created_at': diary['created_at'].isoformat() if diary['created_at'] else None
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'diaries': diaries_list,
                    'total': diary_count
                }
            })
        else:
            # 没有日记的情况
            return jsonify({
                'success': True,
                'data': {
                    'diaries': [],
                    'total': 0,
                    'message': '您还没有创建任何日记',
                    'suggestion': '点击创建按钮开始记录您的第一篇日记'
                }
            })
        
    except Exception as e:
        logger.error(f"获取日记列表失败: {e}")
        # 如果出现异常（如表不存在），也当作没有日记处理
        return jsonify({
            'success': True,
            'data': {
                'diaries': [],
                'total': 0,
                'message': '您还没有创建任何日记',
                'suggestion': '点击创建按钮开始记录您的第一篇日记'
            }
        })