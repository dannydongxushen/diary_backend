from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/diaries', methods=['GET'])
def get_diaries():
    return jsonify({
        'success': True,
        'diaries': [],
        'message': '获取日记列表成功'
    })

@app.route('/api/diaries', methods=['POST'])
def create_diary():
    data = request.get_json()
    return jsonify({
        'success': True,
        'message': '日记创建成功',
        'data': data
    })

app = app