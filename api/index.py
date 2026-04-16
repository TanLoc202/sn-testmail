from flask import Flask

# Khởi tạo ứng dụng
app = Flask(__name__)

# Định nghĩa điều hướng (route)
@app.route('/')
def hello_world():
    return 'Chào mừng bạn đến với ứng dụng Flask!'

# Chạy ứng dụng
if __name__ == '__main__':
    app.run(debug=True)