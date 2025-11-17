# auth.py - 精简版，只处理身份认证
from flask import Blueprint, request, jsonify, current_app
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.config import query_one, execute

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        # 记录原始请求数据
        raw_data = request.get_data(as_text=True)
        current_app.logger.info(f"注册请求数据: {raw_data}")  

        data = request.get_json()
        
        # 验证必需字段
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': '用户名和密码为必填项'
            }), 400
        
        username = data.get('username').strip()
        password = data.get('password')
        nickname = data.get('name', '').strip() or username
        email = data.get('email', '').strip() or None

        # 验证用户名长度
        if len(username) > 50:
            return jsonify({
                'success': False,
                'error': '用户名不能超过50个字符'
            }), 400
        
        # 验证密码长度
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': '密码至少需要6个字符'
            }), 400
        
        # 检查用户名是否已存在
        existing_user = query_one("SELECT user_id FROM users WHERE username = %s", (username,))
        if existing_user:
            return jsonify({
                'success': False,
                'error': '该用户名已被使用'
            }), 409
        
        # 如果提供了邮箱，检查邮箱是否已存在
        if email:
            existing_email = query_one("SELECT user_id FROM users WHERE email = %s", (email,))
            if existing_email:
                return jsonify({
                    'success': False,
                    'error': '该邮箱已被注册'
                }), 409
        
        # 创建新用户
        password_hash = generate_password_hash(password)
        insert_query = """
        INSERT INTO users (username, nickname, password_hash, email)
        VALUES (%s, %s, %s, %s)
        """
        affected = execute(insert_query, (username, nickname, password_hash, email))
        
        if affected == 0:
            return jsonify({
                'success': False,
                'error': '用户注册失败'
            }), 500
        
        # 获取新创建的用户ID
        new_user = query_one("SELECT user_id FROM users WHERE username = %s", (username,))
        user_id = new_user['user_id']
        
        # 生成 JWT token
        token = jwt.encode({
            'user_id': user_id,
            'username': username,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': {
                'user': {
                    'id': user_id,
                    'username': username,
                    'nickname': nickname
                },
                'token': token
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"注册错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '注册过程中发生错误'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': '用户名和密码为必填项'
            }), 400
        
        username = data.get('username').strip()
        password = data.get('password')
        
        # 查找用户
        user = query_one("""
            SELECT user_id, username, nickname, password_hash
            FROM users WHERE username = %s
        """, (username,))
        
        if not user:
            return jsonify({
                'success': False,
                'error': '用户名或密码错误'
            }), 401
        
        # 验证密码
        if not check_password_hash(user['password_hash'], password):
            return jsonify({
                'success': False,
                'error': '用户名或密码错误'
            }), 401
        
        # 生成 JWT token
        token = jwt.encode({
            'user_id': user['user_id'],
            'username': user['username'],
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'user': {
                    'id': user['user_id'],
                    'username': user['username'],
                    'nickname': user['nickname']
                },
                'token': token
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"登录错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '登录过程中发生错误'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        # 对于 JWT token，通常前端只需要删除存储的 token 即可
        # 如果需要服务端实现 token 黑名单，可以在这里添加逻辑
        
        # 简单返回成功，由前端删除 token
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
        
    except Exception as e:
        current_app.logger.error(f"登出错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '登出过程中发生错误'
        }), 500