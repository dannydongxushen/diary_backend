from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
import sys
import traceback
from datetime import datetime

# 详细的日志配置
logging.basicConfig(
    level=logging.DEBUG,  # 设置为 DEBUG 级别以获取更多信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # 确保日志输出到标准输出
    ]
)
logger = logging.getLogger(__name__)

# 记录应用启动信息
logger.info("=" * 60)
logger.info("🚀 启动 Vercel 后端测试版")
logger.info(f"📁 当前工作目录: {os.getcwd()}")
logger.info(f"📁 文件列表: {os.listdir('.')}")
logger.info("=" * 60)

app = Flask(__name__)

# 简化配置 - 开发测试版使用固定密钥
app.config['SECRET_KEY'] = 'vercel-test-key-2024-change-in-production'
logger.info("🔐 应用密钥配置完成")

# 简化 CORS - 允许所有来源（测试用）
CORS(app)
logger.info("🔓 CORS: 允许所有来源（测试环境）")

# 添加请求日志中间件
@app.before_request
def log_request_info():
    logger.debug(f"📥 收到请求: {request.method} {request.path}")
    logger.debug(f"📥 请求头: {dict(request.headers)}")
    logger.debug(f"📥 客户端IP: {request.remote_addr}")
    if request.args:
        logger.debug(f"📥 查询参数: {request.args.to_dict()}")
    if request.is_json:
        try:
            logger.debug(f"📥 请求体 (JSON): {request.get_json()}")
        except:
            logger.debug(f"📥 请求体 (原始): {request.get_data(as_text=True)}")

@app.after_request
def log_response_info(response):
    logger.debug(f"📤 发送响应: {response.status_code}")
    return response

# 注册认证蓝图
try:
    logger.info("🔄 尝试导入认证蓝图...")
    from api import auth_bp
    logger.info("✅ 认证蓝图导入成功")
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    logger.info("✅ 认证蓝图注册成功，URL前缀: /api/auth")
    
    # 检查蓝图路由
    for rule in app.url_map.iter_rules():
        if 'auth' in rule.rule:
            logger.info(f"🔗 注册的路由: {rule.rule} -> {rule.endpoint}")
            
except Exception as e:
    logger.error(f"❌ 蓝图注册失败: {e}")
    logger.error(f"📋 异常详情: {traceback.format_exc()}")
    
    # 检查 api 目录是否存在
    api_dir_exists = os.path.exists('api')
    logger.info(f"📁 api 目录存在: {api_dir_exists}")
    if api_dir_exists:
        logger.info(f"📁 api 目录内容: {os.listdir('api')}")

# 根路径
@app.route('/')
def root():
    logger.info("📍 访问根路径")
    # 显示所有已注册的路由
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': rule.rule
        })
    
    return jsonify({
        'message': '日记应用后端 API - Vercel 测试版',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'routes': routes,
        'endpoints': {
            'health': '/api/health',
            'server_info': '/api/server-info', 
            'db_test': '/api/db-test',
            'user_stats': '/api/user-stats',
            'auth_register': '/api/auth/register',
            'auth_login': '/api/auth/login',
            'auth_profile': '/api/auth/profile'
        }
    })

# 健康检查
@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("❤️  健康检查请求")
    return jsonify({
        'status': 'healthy', 
        'service': 'diary-app-backend',
        'timestamp': datetime.now().isoformat()
    })

# 服务器信息
@app.route('/api/server-info', methods=['GET'])
def server_info():
    logger.info("🌐 服务器信息请求")
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    logger.debug(f"🌐 客户端IP: {client_ip}")
    logger.debug(f"🌐 User-Agent: {user_agent}")
    
    return jsonify({
        'environment': 'vercel-test',
        'client_ip': client_ip,
        'user_agent': user_agent,
        'timestamp': datetime.now().isoformat()
    })

# 数据库连接测试
@app.route('/api/db-test', methods=['GET'])
def db_test():
    logger.info("💾 数据库测试请求")
    try:
        logger.debug("🔄 尝试导入数据库连接函数...")
        from api.auth import get_db_connection
        logger.debug("✅ 数据库连接函数导入成功")
        
        logger.debug("🔄 尝试建立数据库连接...")
        connection = get_db_connection()
        
        if connection and connection.is_connected():
            logger.info("✅ 数据库连接成功")
            
            cursor = connection.cursor()
            cursor.execute("SELECT 1 as test_value, NOW() as server_time")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            logger.info(f"✅ 数据库查询成功: {result}")
            
            return jsonify({
                'status': 'success',
                'database': 'connected',
                'test_result': {
                    'test_value': result[0],
                    'server_time': result[1].isoformat() if result[1] else None
                },
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.error("❌ 数据库连接失败")
            return jsonify({
                'status': 'error', 
                'message': '数据库连接失败',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"❌ 数据库测试错误: {str(e)}")
        logger.error(f"📋 异常详情: {traceback.format_exc()}")
        return jsonify({
            'status': 'error', 
            'message': f'数据库错误: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# 用户统计（测试数据库操作）
@app.route('/api/user-stats', methods=['GET'])
def user_stats():
    logger.info("📊 用户统计请求")
    try:
        from api.auth import get_db_connection
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 获取用户数量
        cursor.execute("SELECT COUNT(*) as user_count FROM users")
        user_count = cursor.fetchone()['user_count']
        logger.info(f"📊 用户数量: {user_count}")
        
        # 获取最新注册用户
        cursor.execute("SELECT username, created_at FROM users ORDER BY created_at DESC LIMIT 5")
        recent_users = cursor.fetchall()
        logger.info(f"📊 最近用户: {len(recent_users)} 个")
        
        cursor.close()
        connection.close()
        
        # 转换日期格式
        for user in recent_users:
            if user['created_at']:
                user['created_at'] = user['created_at'].isoformat()
        
        return jsonify({
            'user_count': user_count,
            'recent_users': recent_users,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 用户统计错误: {str(e)}")
        logger.error(f"📋 异常详情: {traceback.format_exc()}")
        return jsonify({
            'error': f'获取用户统计失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# 路由调试端点
@app.route('/api/debug/routes', methods=['GET'])
def debug_routes():
    """调试端点 - 显示所有已注册的路由"""
    logger.info("🐛 路由调试请求")
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': rule.rule,
            'is_leaf': rule.is_leaf
        })
    
    logger.info(f"🐛 已注册路由数量: {len(routes)}")
    for route in routes:
        logger.info(f"🐛 路由: {route['path']} -> {route['endpoint']}")
    
    return jsonify({
        'total_routes': len(routes),
        'routes': routes,
        'timestamp': datetime.now().isoformat()
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"❌ 404 错误: {request.path}")
    return jsonify({
        'status': 'error',
        'message': f'请求的资源不存在: {request.path}',
        'available_endpoints': [
            '/api/health',
            '/api/server-info',
            '/api/db-test',
            '/api/user-stats',
            '/api/auth/register',
            '/api/auth/login',
            '/api/debug/routes'
        ],
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ 500 内部服务器错误: {str(error)}")
    logger.error(f"📋 异常详情: {traceback.format_exc()}")
    return jsonify({
        'status': 'error',
        'message': '服务器内部错误',
        'timestamp': datetime.now().isoformat()
    }), 500

# Vercel 需要这个变量
application = app

# 记录应用启动完成
logger.info("✅ Flask 应用配置完成")
logger.info("🔗 注册的路由:")
for rule in app.url_map.iter_rules():
    if not rule.rule.startswith('/static'):
        logger.info(f"  {rule.rule} -> {rule.endpoint}")

# 本地开发直接运行
if __name__ == '__main__':
    logger.info("🚀 启动本地开发服务器")
    logger.info("📍 本地访问: http://localhost:5000")
    logger.info("🌐 API 地址: http://localhost:5000/api/...")
    logger.info("🐛 调试路由: http://localhost:5000/api/debug/routes")
    app.run(host='0.0.0.0', port=5000, debug=True)