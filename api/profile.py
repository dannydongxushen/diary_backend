# profile.py - 用户资料管理
from flask import Blueprint, request, jsonify, current_app
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from database.config import query_one, execute

# 创建用户资料蓝图
profile_bp = Blueprint('profile', __name__)

def get_current_user_from_token():
    """从token中提取当前用户信息的公共函数"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, '缺少认证令牌'
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, '令牌已过期'
    except jwt.InvalidTokenError:
        return None, '无效令牌'

@profile_bp.route('/profile', methods=['GET'])
def get_profile():
    """获取用户完整资料"""
    payload, error = get_current_user_from_token()
    if error:
        return jsonify({'success': False, 'error': error}), 401
    
    user = query_one("""
        SELECT user_id, username, nickname, email, phone, is_verified, created_at, updated_at
        FROM users WHERE user_id = %s
    """, (payload['user_id'],))
    
    if not user:
        return jsonify({'success': False, 'error': '用户不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': {
            'user': {
                'id': user['user_id'],
                'username': user['username'],
                'nickname': user['nickname'],
                'email': user['email'],
                'phone': user['phone'],
                'is_verified': bool(user.get('is_verified', False)),
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
            }
        }
    })

@profile_bp.route('/update-password', methods=['PUT'])
def update_password():
    """修改密码"""
    payload, error = get_current_user_from_token()
    if error:
        return jsonify({'success': False, 'error': error}), 401
    
    data = request.get_json()
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({
            'success': False,
            'error': '当前密码和新密码为必填项'
        }), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    # 验证新密码长度
    if len(new_password) < 6:
        return jsonify({
            'success': False,
            'error': '新密码至少需要6个字符'
        }), 400
    
    # 获取用户当前密码哈希
    user = query_one(
        "SELECT password_hash FROM users WHERE user_id = %s", 
        (payload['user_id'],)
    )
    
    if not user:
        return jsonify({'success': False, 'error': '用户不存在'}), 404
    
    # 验证当前密码是否正确
    if not check_password_hash(user['password_hash'], current_password):
        return jsonify({
            'success': False,
            'error': '当前密码错误'
        }), 401
    
    # 更新密码
    new_password_hash = generate_password_hash(new_password)
    update_query = """
        UPDATE users 
        SET password_hash = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE user_id = %s
    """
    affected = execute(update_query, (new_password_hash, payload['user_id']))
    
    if affected == 0:
        return jsonify({
            'success': False,
            'error': '密码更新失败'
        }), 500
    
    return jsonify({
        'success': True,
        'message': '密码更新成功'
    })

@profile_bp.route('/update-email', methods=['PUT'])
def update_email():
    """添加或修改邮箱"""
    payload, error = get_current_user_from_token()
    if error:
        return jsonify({'success': False, 'error': error}), 401
    
    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({
            'success': False,
            'error': '邮箱为必填项'
        }), 400
    
    new_email = data.get('email').strip().lower()
    
    # 验证邮箱格式（简单验证）
    if '@' not in new_email:
        return jsonify({
            'success': False,
            'error': '邮箱格式不正确'
        }), 400
    
    # 检查邮箱是否已被其他用户使用
    existing_email = query_one(
        "SELECT user_id FROM users WHERE email = %s AND user_id != %s", 
        (new_email, payload['user_id'])
    )
    if existing_email:
        return jsonify({
            'success': False,
            'error': '该邮箱已被其他用户使用'
        }), 409
    
    # 更新邮箱
    update_query = """
        UPDATE users 
        SET email = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE user_id = %s
    """
    affected = execute(update_query, (new_email, payload['user_id']))
    
    if affected == 0:
        return jsonify({
            'success': False,
            'error': '邮箱更新失败'
        }), 500
    
    # 获取更新后的用户信息
    user = query_one("""
        SELECT user_id, username, nickname, email, phone, is_verified, created_at, updated_at
        FROM users WHERE user_id = %s
    """, (payload['user_id'],))
    
    return jsonify({
        'success': True,
        'message': '邮箱更新成功',
        'data': {
            'user': {
                'id': user['user_id'],
                'username': user['username'],
                'nickname': user['nickname'],
                'email': user['email'],
                'phone': user['phone'],
                'is_verified': bool(user.get('is_verified', False)),
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
            }
        }
    })

@profile_bp.route('/update-phone', methods=['PUT'])
def update_phone():
    """添加或修改手机号"""
    payload, error = get_current_user_from_token()
    if error:
        return jsonify({'success': False, 'error': error}), 401
    
    data = request.get_json()
    if not data or not data.get('phone'):
        return jsonify({
            'success': False,
            'error': '手机号为必填项'
        }), 400
    
    new_phone = data.get('phone').strip()
    
    # 简单验证手机号格式（可根据需求调整）
    if not new_phone.isdigit() or len(new_phone) < 10:
        return jsonify({
            'success': False,
            'error': '手机号格式不正确'
        }), 400
    
    # 检查手机号是否已被其他用户使用
    existing_phone = query_one(
        "SELECT user_id FROM users WHERE phone = %s AND user_id != %s", 
        (new_phone, payload['user_id'])
    )
    if existing_phone:
        return jsonify({
            'success': False,
            'error': '该手机号已被其他用户使用'
        }), 409
    
    # 更新手机号
    update_query = """
        UPDATE users 
        SET phone = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE user_id = %s
    """
    affected = execute(update_query, (new_phone, payload['user_id']))
    
    if affected == 0:
        return jsonify({
            'success': False,
            'error': '手机号更新失败'
        }), 500
    
    # 获取更新后的用户信息
    user = query_one("""
        SELECT user_id, username, nickname, email, phone, is_verified, created_at, updated_at
        FROM users WHERE user_id = %s
    """, (payload['user_id'],))
    
    return jsonify({
        'success': True,
        'message': '手机号更新成功',
        'data': {
            'user': {
                'id': user['user_id'],
                'username': user['username'],
                'nickname': user['nickname'],
                'email': user['email'],
                'phone': user['phone'],
                'is_verified': bool(user.get('is_verified', False)),
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
            }
        }
    })

@profile_bp.route('/update-profile', methods=['PUT'])
def update_profile():
    """更新用户基本信息（昵称等）"""
    payload, error = get_current_user_from_token()
    if error:
        return jsonify({'success': False, 'error': error}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据不能为空'
        }), 400
    
    # 构建更新字段和参数
    update_fields = []
    update_params = []
    
    # 昵称更新
    if 'nickname' in data:
        nickname = data.get('nickname', '').strip()
        if nickname:
            update_fields.append("nickname = %s")
            update_params.append(nickname)
    
    # 如果没有提供任何可更新的字段
    if not update_fields:
        return jsonify({
            'success': False,
            'error': '没有提供可更新的字段'
        }), 400
    
    # 添加更新时间
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    # 构建更新查询
    update_query = f"""
        UPDATE users 
        SET {', '.join(update_fields)} 
        WHERE user_id = %s
    """
    update_params.append(payload['user_id'])
    
    # 执行更新
    affected = execute(update_query, tuple(update_params))
    
    if affected == 0:
        return jsonify({
            'success': False,
            'error': '资料更新失败'
        }), 500
    
    # 获取更新后的用户信息
    user = query_one("""
        SELECT user_id, username, nickname, email, phone, is_verified, created_at, updated_at
        FROM users WHERE user_id = %s
    """, (payload['user_id'],))
    
    return jsonify({
        'success': True,
        'message': '资料更新成功',
        'data': {
            'user': {
                'id': user['user_id'],
                'username': user['username'],
                'nickname': user['nickname'],
                'email': user['email'],
                'phone': user['phone'],
                'is_verified': bool(user.get('is_verified', False)),
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
            }
        }
    })

@profile_bp.route('/me', methods=['GET'])
def get_current_user():
    """获取当前用户信息（/profile的别名）"""
    return get_profile()