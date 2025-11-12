from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许前端访问

@app.route('/')
def home():
    return jsonify({
        'message': '日记应用后端服务运行正常',
        'status': 'OK',
        'version': '1.0.0'
    })

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'})

# Vercel 需要这个
app = app