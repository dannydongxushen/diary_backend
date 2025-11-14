# auth.py - 直接连接版本
from flask import Blueprint, request, jsonify, current_app
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os
import time

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    """获取数据库连接 - 启用 SSL 连接"""
    try:
        connection = mysql.connector.connect(
            host='mysql2.sqlpub.com',
            port=3307,
            database='dxshenwebappdb',
            user='dxshen',
            password='iXR2bGPwZ9rmzrhm',
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            use_unicode=True,
            autocommit=True,
            connect_timeout=10,
            # 启用 SSL 而不是禁用
            ssl_disabled=False,
            # 对于公共数据库，通常使用默认的 SSL 配置即可
            ssl_verify_identity=False  # 不验证证书身份，适用于大多数公共数据库
        )
        return connection
    except Error as e:
        current_app.logger.error(f"数据库连接失败: {e}")
        return None

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    connection = None
    cursor = None
    try:
        # 记录原始请求数据
        raw_data = request.get_data(as_text=True)
        current_app.logger.info(f"原始请求数据: {raw_data}")  

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

        # 添加详细的调试信息
        current_app.logger.info(f"解析后的数据 - 用户名: '{username}' (长度: {len(username)}), 昵称: '{nickname}' (长度: {len(nickname)})")
        
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
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': '数据库连接失败'
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # 检查用户名是否已存在
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '该用户名已被使用'
            }), 409
        
        # 如果提供了邮箱，检查邮箱是否已存在
        if email:
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
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
        cursor.execute(insert_query, (username, nickname, password_hash, email))
        user_id = cursor.lastrowid
        
        connection.commit()
        
        # 生成 JWT token
        token = jwt.encode({
            'user_id': user_id,
            'username': username,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        # 获取完整的用户信息
        cursor.execute("""
            SELECT user_id, username, nickname, email, phone, created_at, updated_at, is_verified
            FROM users WHERE user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': {
                'user': {
                    'id': user['user_id'],
                    'username': user['username'],
                    'nickname': user['nickname'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'is_verified': bool(user['is_verified']),
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
                },
                'token': token
            }
        }), 201
        
    except Error as e:
        current_app.logger.error(f"数据库错误: {str(e)}")
        if connection:
            connection.rollback()
        return jsonify({
            'success': False,
            'error': '注册过程中发生数据库错误'
        }), 500
    except Exception as e:
        current_app.logger.error(f"注册错误: {str(e)}")
        if connection:
            connection.rollback()
        return jsonify({
            'success': False,
            'error': '注册过程中发生错误'
        }), 500
    finally:
        # 资源释放
        if cursor:
            try:
                cursor.close()
                current_app.logger.info("游标已关闭")
            except:
                pass
        
        if connection:
            try:
                if connection.is_connected():
                    connection.close()
                    current_app.logger.info("连接已关闭")
            except:
                pass

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    connection = None
    cursor = None
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
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': '数据库连接失败'
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # 查找用户
        cursor.execute("""
            SELECT user_id, username, nickname, email, password_hash, phone, is_verified, created_at
            FROM users WHERE username = %s
        """, (username,))
        user = cursor.fetchone()
        
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
                    'nickname': user['nickname'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'is_verified': bool(user['is_verified']),
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None
                },
                'token': token
            }
        })
        
    except Error as e:
        current_app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '登录过程中发生数据库错误'
        }), 500
    except Exception as e:
        current_app.logger.error(f"登录错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '登录过程中发生错误'
        }), 500
    finally:
        # 资源释放
        if cursor:
            try:
                cursor.close()
            except:
                pass
        
        if connection:
            try:
                if connection.is_connected():
                    connection.close()
            except:
                pass

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """获取用户信息（需要认证）"""
    connection = None
    cursor = None
    try:
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': '缺少认证令牌'
            }), 401
        
        token = auth_header.split(' ')[1]
        
        # 验证token
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': '令牌已过期'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': '无效令牌'
            }), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': '数据库连接失败'
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # 查找用户
        cursor.execute("""
            SELECT user_id, username, nickname, email, phone, is_verified, created_at, updated_at
            FROM users WHERE user_id = %s
        """, (payload['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user['user_id'],
                    'username': user['username'],
                    'nickname': user['nickname'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'is_verified': bool(user['is_verified']),
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
                }
            }
        })
        
    except Error as e:
        current_app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取用户信息时发生数据库错误'
        }), 500
    except Exception as e:
        current_app.logger.error(f"获取用户信息错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取用户信息失败'
        }), 500
    finally:
        # 资源释放
        if cursor:
            try:
                cursor.close()
            except:
                pass
        
        if connection:
            try:
                if connection.is_connected():
                    connection.close()
            except:
                pass

@auth_bp.route('/update-email', methods=['PUT'])
def update_email():
    """更新用户邮箱"""
    connection = None
    cursor = None
    try:
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': '缺少认证令牌'
            }), 401
        
        token = auth_header.split(' ')[1]
        
        # 验证token
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': '令牌已过期'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': '无效令牌'
            }), 401
        
        # 获取新邮箱
        data = request.get_json()
        if not data or not data.get('email'):
            return jsonify({
                'success': False,
                'error': '邮箱为必填项'
            }), 400
        
        new_email = data.get('email').strip().lower()
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'error': '数据库连接失败'
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # 检查邮箱是否已被其他用户使用
        cursor.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (new_email, payload['user_id']))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '该邮箱已被其他用户使用'
            }), 409
        
        # 更新邮箱
        update_query = "UPDATE users SET email = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s"
        cursor.execute(update_query, (new_email, payload['user_id']))
        connection.commit()
        
        # 获取更新后的用户信息
        cursor.execute("""
            SELECT user_id, username, nickname, email, phone, is_verified, created_at, updated_at
            FROM users WHERE user_id = %s
        """, (payload['user_id'],))
        user = cursor.fetchone()
        
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
                    'is_verified': bool(user['is_verified']),
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
                }
            }
        })
        
    except Error as e:
        current_app.logger.error(f"数据库错误: {str(e)}")
        if connection:
            connection.rollback()
        return jsonify({
            'success': False,
            'error': '更新邮箱时发生数据库错误'
        }), 500
    except Exception as e:
        current_app.logger.error(f"更新邮箱错误: {str(e)}")
        if connection:
            connection.rollback()
        return jsonify({
            'success': False,
            'error': '更新邮箱失败'
        }), 500
    finally:
        # 资源释放
        if cursor:
            try:
                cursor.close()
            except:
                pass
        
        if connection:
            try:
                if connection.is_connected():
                    connection.close()
            except:
                pass

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """获取当前用户信息（get_profile的别名）"""
    return get_profile()

@auth_bp.route('/debug/connection-test', methods=['GET'])
def debug_connection_test():
    """测试数据库连接"""
    connection = None
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return jsonify({
                'success': True,
                'message': '数据库连接正常',
                'data': {
                    'test_query': 'SELECT 1',
                    'result': result[0] if result else None
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': '数据库连接失败'
            }), 500
    except Error as e:
        return jsonify({
            'success': False,
            'error': f'数据库连接测试失败: {str(e)}'
        }), 500
    finally:
        if connection and connection.is_connected():
            connection.close()

@auth_bp.route('/debug/connection-stats', methods=['GET'])
def debug_connection_stats():
    """获取数据库连接统计信息"""
    connection = None
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # 获取数据库版本
            cursor.execute("SELECT VERSION() as version")
            version_result = cursor.fetchone()
            
            # 获取用户数量
            cursor.execute("SELECT COUNT(*) as user_count FROM users")
            user_count_result = cursor.fetchone()
            
            # 获取数据库状态信息
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            threads_result = cursor.fetchone()
            
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': '数据库连接统计信息',
                'data': {
                    'database_version': version_result['version'] if version_result else 'Unknown',
                    'user_count': user_count_result['user_count'] if user_count_result else 0,
                    'threads_connected': threads_result['Value'] if threads_result else 'Unknown',
                    'connection_time': datetime.datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': '数据库连接失败'
            }), 500
    except Error as e:
        return jsonify({
            'success': False,
            'error': f'获取数据库统计信息失败: {str(e)}'
        }), 500
    finally:
        if connection and connection.is_connected():
            connection.close()