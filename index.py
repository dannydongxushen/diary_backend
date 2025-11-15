from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
import sys
from datetime import datetime

# 生产环境日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# CORS 配置
if os.environ.get('ENVIRONMENT') == 'production':
    CORS(app, origins=['https://your-domain.com'])
else:
    CORS(app)

# 请求日志（简化版）
@app.before_request
def log_request():
    if request.path != '/api/health':  # 避免健康检查日志过多
        logger.info(f"{request.method} {request.path} - {request.remote_addr}")

# 注册蓝图
try:
    from api import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    logger.info("认证蓝图注册成功")
except Exception as e:
    logger.error(f"蓝图注册失败: {e}")

# 根路径
@app.route('/')
def root():
    return jsonify({
        'message': '日记应用后端 API',
        'status': 'running', 
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

# 健康检查（保留）
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # 生产环境关闭 debug