from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
import sys
from datetime import datetime

# 生产环境日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 添加了name
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 安全配置（优化版）
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    if os.environ.get('ENVIRONMENT') == 'production':
        raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
    else:
        app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
        logger.warning("使用开发环境的默认 SECRET_KEY，生产环境请设置环境变量")

# CORS 配置
if os.environ.get('ENVIRONMENT') == 'production':
    CORS(app, origins=[
        'https://smartour.netlify.app',
        'https://test-login--smartour.netlify.app',
        'http://localhost:3000',
        'http://localhost:5173', 
        'http://localhost:8080',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:8080'
    ])
else:
    CORS(app)

# 请求日志
@app.before_request
def log_request():
    if request.path != '/api/health':
        logger.info(f"{request.method} {request.path} - {request.remote_addr} - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")

# 注册蓝图
try:
    # 注册认证蓝图
    from api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    logger.info("认证蓝图注册成功")    
except Exception as e:
    logger.error(f"认证蓝图注册失败: {e}")
    
try:
    # 注册日记蓝图
    from api.diaries import diaries_bp
    app.register_blueprint(diaries_bp, url_prefix='/api/diaries')
    logger.info("日记蓝图注册成功") 
except Exception as e:
    logger.error(f"日记蓝图注册失败: {e}")
    
try:        
    # 注册用户资料蓝图
    from api.profile import profile_bp
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    logger.info("用户资料蓝图注册成功")         
except Exception as e:
    logger.error(f"用户资料蓝图注册失败: {e}")

# 根路径
@app.route('/')
def root():
    return jsonify({
        'message': '日记应用后端 API',
        'status': 'running', 
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('ENVIRONMENT', 'development')
    })

# 健康检查
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'service': 'diary-backend'
    })

# 错误处理（优化版）
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}")
    
    # 开发环境返回更详细的错误信息
    if os.environ.get('ENVIRONMENT') != 'production':
        return jsonify({
            'error': 'Internal server error',
            'detail': str(error) if error else 'Unknown error',
            'path': request.path
        }), 500
    else:
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

application = app

if __name__ == '__main__':
    # 根据环境变量控制启动参数
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    host = '0.0.0.0' if os.environ.get('ENVIRONMENT') == 'production' else '127.0.0.1'
    
    logger.info(f"启动Flask应用 - 环境: {os.environ.get('ENVIRONMENT', 'development')}, Debug: {debug_mode}")
    
    app.run(host=host, port=5000, debug=debug_mode)