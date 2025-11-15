from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging

# 基础日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # 简化配置 - 开发测试版使用固定密钥
    app.config['SECRET_KEY'] = 'vercel-test-key-2024-change-in-production'
    
    # 简化 CORS - 允许所有来源（测试用）
    CORS(app)
    logger.info("🔓 CORS: 允许所有来源（测试环境）")
    
    # 注册认证蓝图
    try:
        from api import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        logger.info("✅ 认证蓝图注册成功")
    except Exception as e:
        logger.error(f"❌ 蓝图注册失败: {e}")
    
    # 测试端点 - 验证服务器运行状态
    @app.route('/')
    def root():
        return jsonify({
            'message': '日记应用后端 API - Vercel 测试版',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'server_info': '/api/server-info', 
                'db_test': '/api/db-test',
                'auth_register': '/api/auth/register',
                'auth_login': '/api/auth/login'
            }
        })
    
    # 健康检查
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'diary-app-backend'})
    
    # 服务器信息
    @app.route('/api/server-info')
    def server_info():
        return jsonify({
            'environment': 'vercel-test',
            'client_ip': request.headers.get('X-Forwarded-For', request.remote_addr),
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        })
    
    # 数据库连接测试
    @app.route('/api/db-test')
    def db_test():
        try:
            from api.auth import get_db_connection
            connection = get_db_connection()
            if connection and connection.is_connected():
                cursor = connection.cursor()
                cursor.execute("SELECT 1 as test_value, NOW() as server_time")
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                
                return jsonify({
                    'status': 'success',
                    'database': 'connected',
                    'test_result': {
                        'test_value': result[0],
                        'server_time': result[1].isoformat() if result[1] else None
                    }
                })
            else:
                return jsonify({'status': 'error', 'message': '数据库连接失败'}), 500
                
        except Exception as e:
            return jsonify({
                'status': 'error', 
                'message': f'数据库错误: {str(e)}'
            }), 500
    
    # 用户统计（测试数据库操作）
    @app.route('/api/user-stats')
    def user_stats():
        try:
            from api.auth import get_db_connection
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # 获取用户数量
            cursor.execute("SELECT COUNT(*) as user_count FROM users")
            user_count = cursor.fetchone()['user_count']
            
            # 获取最新注册用户
            cursor.execute("SELECT username, created_at FROM users ORDER BY created_at DESC LIMIT 5")
            recent_users = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            # 转换日期格式
            for user in recent_users:
                if user['created_at']:
                    user['created_at'] = user['created_at'].isoformat()
            
            return jsonify({
                'user_count': user_count,
                'recent_users': recent_users
            })
            
        except Exception as e:
            return jsonify({'error': f'获取用户统计失败: {str(e)}'}), 500
    
    return app

# 创建应用实例
app = create_app()

# Vercel 需要这个变量
application = app

# 本地开发直接运行
if __name__ == '__main__':
    logger.info("🚀 启动 Vercel 测试版后端")
    logger.info("📍 本地访问: http://localhost:5000")
    logger.info("🌐 API 地址: http://localhost:5000/api/...")
    app.run(host='0.0.0.0', port=5000, debug=True)