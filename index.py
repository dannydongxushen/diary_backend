from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import logging
from datetime import datetime, timezone  # 添加 timezone 导入


# 创建 Flask 应用实例
app = Flask(__name__)

# 配置 CORS
CORS(app, origins=[
    "http://localhost:3000",  # 前端开发服务器
    "http://localhost:5000",  # 后端开发服务器
    "https://dxshenwebtestapp.netlify.app"  # 生产前端地址
])

# 基础配置
app.config['JSON_SORT_KEYS'] = False  # 保持 JSON 响应顺序
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET', 'dev-secret-key')

# 配置日志（只保留一个配置）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 健康检查端点
@app.route('/')
def home():
    """服务健康检查端点"""
    return jsonify({
        'success': True,
        'message': '日记应用后端服务运行正常',
        'timestamp': datetime.now(timezone.utc).isoformat(),  # 修复：使用 timezone.utc
        'version': '1.0.0',
        'service': 'diary-backend'
    })

@app.route('/api/health')
def health_check():
    """详细的健康检查端点"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),  # 修复：使用 timezone.utc
        'service': 'diary-backend',
        'environment': os.environ.get('ENVIRONMENT', 'development')
    }
    
    # 可以在这里添加数据库连接检查等
    try:
        # 后续可以添加数据库连接测试
        health_status['database'] = 'unknown'  # 暂时标记为未知
    except Exception as e:
        health_status['database'] = 'unhealthy'
        health_status['database_error'] = str(e)
    
    return jsonify(health_status)

# 基础 API 信息端点
@app.route('/api')
def api_info():
    """API 基本信息端点"""
    return jsonify({
        'success': True,
        'data': {
            'name': '日记应用 API',
            'version': '1.0.0',
            'description': '个人日记应用的后端服务',
            'endpoints': {
                'auth': '/api/auth',
                'diaries': '/api/diaries',
                'health': '/api/health'
            }
        }
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({
        'success': False,
        'error': {
            'code': 'NOT_FOUND',
            'message': '请求的资源不存在',
            'path': request.path
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    logger.error(f"服务器内部错误: {str(error)}")
    return jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': '服务器内部错误，请稍后重试'
        }
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    """405 错误处理"""
    return jsonify({
        'success': False,
        'error': {
            'code': 'METHOD_NOT_ALLOWED',
            'message': '不支持的请求方法'
        }
    }), 405

# 请求前处理
@app.before_request
def before_request():
    """每个请求前的处理"""
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")

# 请求后处理
@app.after_request
def after_request(response):
    """每个请求后的处理"""
    response.headers['X-Service'] = 'diary-backend'
    response.headers['X-Version'] = '1.0.0'
    return response

# 导入认证路由（下一步实现）
try:
    from api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    logger.info("认证路由加载成功")
except ImportError as e:
    logger.warning(f"认证路由暂未实现: {e}")

# 导入日记路由（后续实现）
try:
    from api.diaries import diaries_bp
    app.register_blueprint(diaries_bp, url_prefix='/api/diaries')
    logger.info("日记路由加载成功")
except ImportError as e:
    logger.warning(f"日记路由暂未实现: {e}")

# 本地开发运行
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"启动日记后端服务，端口: {port}, 调试模式: {debug}")
    print("=== 准备启动服务器 ===")
    app.run(host='0.0.0.0', port=port, debug=debug)